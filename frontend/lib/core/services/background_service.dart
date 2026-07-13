import 'dart:async';
import 'dart:ui';

import 'package:dio/dio.dart';
import 'package:flutter_background_service/flutter_background_service.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/constants/app_constants.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Notification channel setup
// ─────────────────────────────────────────────────────────────────────────────

const _notifChannelId = 'deriv_bot_service';
const _notifChannelName = 'Deriv AI Trader Bot';
const _notifId = 1001;

final FlutterLocalNotificationsPlugin _notifPlugin =
    FlutterLocalNotificationsPlugin();

// ─────────────────────────────────────────────────────────────────────────────
// Initialise the background service
// Call this once in main() before runApp
// ─────────────────────────────────────────────────────────────────────────────

Future<void> initBackgroundService() async {
  final service = FlutterBackgroundService();

  // Create notification channel (Android 8+)
  const AndroidNotificationChannel channel = AndroidNotificationChannel(
    _notifChannelId,
    _notifChannelName,
    description: 'Shows bot status while trading in background',
    importance: Importance.low,         // low = no sound, just persistent icon
    playSound: false,
    showBadge: false,
  );

  await _notifPlugin
      .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin>()
      ?.createNotificationChannel(channel);

  await service.configure(
    androidConfiguration: AndroidConfiguration(
      onStart: onServiceStart,
      autoStart: false,           // only start when user taps Start Bot
      isForegroundMode: true,     // foreground = visible notification = stays alive
      notificationChannelId: _notifChannelId,
      initialNotificationTitle: 'Deriv AI Trader',
      initialNotificationContent: 'Bot is starting...',
      foregroundServiceNotificationId: _notifId,
      foregroundServiceTypes: [AndroidForegroundType.dataSync],
    ),
    iosConfiguration: IosConfiguration(
      autoStart: false,
      onForeground: onServiceStart,
      onBackground: onIosBackground,
    ),
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// iOS background handler (required by the plugin)
// ─────────────────────────────────────────────────────────────────────────────

@pragma('vm:entry-point')
Future<bool> onIosBackground(ServiceInstance service) async {
  return true;
}

// ─────────────────────────────────────────────────────────────────────────────
// Main background service entry point
// Runs in a separate isolate — keeps running with screen off
// ─────────────────────────────────────────────────────────────────────────────

@pragma('vm:entry-point')
void onServiceStart(ServiceInstance service) async {
  DartPluginRegistrant.ensureInitialized();

  // ── Update the persistent notification ───────────────────────────────────
  void updateNotification(String status, String detail) {
    service.invoke('update', {
      'title': 'Deriv AI Trader — $status',
      'content': detail,
    });

    if (service is AndroidServiceInstance) {
      service.setForegroundNotificationInfo(
        title: 'Deriv AI Trader — $status',
        content: detail,
      );
    }
  }

  updateNotification('Starting', 'Connecting to Deriv...');

  // ── Read saved settings ───────────────────────────────────────────────────
  final prefs = await SharedPreferences.getInstance();
  final accessToken = prefs.getString(AppConstants.accessTokenKey) ?? '';
  final symbol = prefs.getString(AppConstants.botSymbolKey) ??
      AppConstants.defaultBotSymbol;
  final accountType = prefs.getString('account_type') ?? 'demo';
  final baseUrl = AppConstants.baseUrl;

  if (accessToken.isEmpty) {
    updateNotification('Error', 'No login session. Open the app to log in.');
    return;
  }

  // ── Start the bot via the backend API ─────────────────────────────────────
  final dio = Dio(BaseOptions(
    baseUrl: '$baseUrl${AppConstants.apiPrefix}',
    headers: {
      'Authorization': 'Bearer $accessToken',
      'Content-Type': 'application/json',
    },
    connectTimeout: const Duration(seconds: 15),
    receiveTimeout: const Duration(seconds: 15),
  ));

  try {
    final r = await dio.post(
      '/trading/start',
      queryParameters: {'symbol': symbol, 'account_type': accountType},
    );
    final status = (r.data as Map<String, dynamic>)['status'] as String?
        ?? 'unknown';
    updateNotification('RUNNING', '$symbol | $accountType');
    service.invoke('status', {'status': status, 'symbol': symbol});
  } catch (e) {
    updateNotification('Error', 'Could not start bot: ${_shortError(e)}');
    return;
  }

  // ── Keep-alive loop — updates notification every 30 seconds ──────────────
  int tick = 0;
  Timer.periodic(const Duration(seconds: 30), (timer) async {
    // Check if service was asked to stop
    if (service is AndroidServiceInstance) {
      if (!await service.isForegroundService()) {
        timer.cancel();
        return;
      }
    }

    tick++;
    try {
      // Ping the bot status endpoint to confirm it is still running
      final r = await dio.get('/trading/status');
      final status = (r.data as Map<String, dynamic>)['status'] as String?
          ?? 'unknown';

      final label = status == 'running'
          ? 'RUNNING'
          : status == 'paused'
              ? 'PAUSED'
              : status;

      updateNotification(label, '$symbol | $accountType | tick $tick');
      service.invoke('status', {'status': status, 'symbol': symbol});
    } catch (_) {
      updateNotification('Checking...', 'Reconnecting...');
    }
  });

  // ── Listen for stop command from the UI ───────────────────────────────────
  service.on('stop').listen((_) async {
    try {
      await dio.post('/trading/stop');
    } catch (_) {}
    service.stopSelf();
  });

  // ── Listen for pause command ──────────────────────────────────────────────
  service.on('pause').listen((_) async {
    try {
      await dio.post('/trading/pause');
      updateNotification('PAUSED', '$symbol | paused');
    } catch (_) {}
  });

  // ── Listen for resume command ─────────────────────────────────────────────
  service.on('resume').listen((_) async {
    try {
      await dio.post('/trading/resume');
      updateNotification('RUNNING', '$symbol | resumed');
    } catch (_) {}
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Public helpers — called from the UI
// ─────────────────────────────────────────────────────────────────────────────

/// Start the background service (and the bot)
Future<void> startBackgroundBot() async {
  final service = FlutterBackgroundService();
  await service.startService();
}

/// Stop the background service (and the bot)
Future<void> stopBackgroundBot() async {
  final service = FlutterBackgroundService();
  service.invoke('stop');
}

/// Pause the bot (service keeps running)
Future<void> pauseBackgroundBot() async {
  final service = FlutterBackgroundService();
  service.invoke('pause');
}

/// Resume the bot
Future<void> resumeBackgroundBot() async {
  final service = FlutterBackgroundService();
  service.invoke('resume');
}

/// Check if background service is currently running
Future<bool> isBackgroundServiceRunning() async {
  final service = FlutterBackgroundService();
  return await service.isRunning();
}

/// Stream of status updates from the background service
Stream<Map<String, dynamic>?> botStatusStream() {
  final service = FlutterBackgroundService();
  return service.on('status');
}

// ─────────────────────────────────────────────────────────────────────────────
// Helper
// ─────────────────────────────────────────────────────────────────────────────

String _shortError(Object e) {
  final s = e.toString();
  if (s.length > 60) return '${s.substring(0, 60)}...';
  return s;
}
