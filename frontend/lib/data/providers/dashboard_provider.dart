import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/constants/app_constants.dart';
import '../../core/services/background_service.dart';
import '../providers/account_type_provider.dart';
import '../providers/bot_symbol_provider.dart';
import '../services/dashboard_service.dart';

final dashboardProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  return ref.read(dashboardServiceProvider).getDashboard();
});

// ── Bot status notifier ───────────────────────────────────────────────────────

class BotStatusNotifier extends StateNotifier<String> {
  final Ref _ref;
  String? _lastError;

  BotStatusNotifier(this._ref) : super('stopped') {
    _syncWithService();
  }

  String? get lastError => _lastError;
  void clearError() => _lastError = null;

  /// On startup check if background service is already running
  Future<void> _syncWithService() async {
    final running = await isBackgroundServiceRunning();
    if (running && mounted) state = 'running';

    // Listen to live status updates from the background service
    botStatusStream().listen((data) {
      if (data != null && mounted) {
        final s = data['status'] as String? ?? state;
        state = s;
      }
    });
  }

  Future<void> startBot() async {
    state = 'connecting';
    _lastError = null;

    try {
      final symbol      = _ref.read(botSymbolProvider);
      final accountType = _ref.read(accountTypeProvider);

      // Save to SharedPreferences so the background service isolate can read them
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(AppConstants.botSymbolKey, symbol);
      await prefs.setString('account_type', accountType);

      // Start the foreground service — this keeps the bot alive with screen off
      await startBackgroundBot();

      if (mounted) state = 'running';
    } catch (e) {
      final msg = e.toString();
      if (msg.contains('token')) {
        _lastError = 'No Deriv token saved. Go to Profile → save your token first.';
      } else if (msg.contains('400')) {
        _lastError = 'Could not start bot. Check your Deriv token in Profile.';
      } else {
        _lastError = 'Bot error. Please try again.';
      }
      if (mounted) state = 'error';
    }
  }

  Future<void> pauseBot() async {
    pauseBackgroundBot();
    if (mounted) state = 'paused';
  }

  Future<void> resumeBot() async {
    resumeBackgroundBot();
    if (mounted) state = 'running';
  }

  Future<void> stopBot() async {
    stopBackgroundBot();
    _lastError = null;
    if (mounted) state = 'stopped';
  }

  void setStatus(String s) {
    if (mounted) state = s;
  }
}

final botStatusProvider =
    StateNotifierProvider<BotStatusNotifier, String>((ref) {
  return BotStatusNotifier(ref);
});
