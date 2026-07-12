import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/dashboard_service.dart';
import '../services/trading_service.dart';

final dashboardProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  return ref.read(dashboardServiceProvider).getDashboard();
});

// ── Bot status ────────────────────────────────────────────────────────────────

class BotStatusNotifier extends StateNotifier<String> {
  final Ref _ref;
  String? _lastError;

  BotStatusNotifier(this._ref) : super('stopped');

  String? get lastError => _lastError;

  Future<void> startBot() async {
    state = 'connecting';
    _lastError = null;
    try {
      final result = await _ref.read(tradingServiceProvider).startBot();
      state = result['status'] as String? ?? 'stopped';
    } catch (e) {
      // Extract friendly error message
      final msg = e.toString();
      if (msg.contains('invalid') || msg.contains('token')) {
        _lastError = 'Deriv token is invalid. Please update your token in Profile.';
      } else if (msg.contains('No Deriv API token')) {
        _lastError = 'No Deriv token found. Go to Profile and save your token first.';
      } else {
        _lastError = 'Failed to start bot. Please check your Deriv token.';
      }
      state = 'stopped';
    }
  }

  Future<void> pauseBot() async {
    try {
      final result = await _ref.read(tradingServiceProvider).pauseBot();
      state = result['status'] as String? ?? 'paused';
    } catch (_) {}
  }

  Future<void> resumeBot() async {
    try {
      final result = await _ref.read(tradingServiceProvider).resumeBot();
      state = result['status'] as String? ?? 'running';
    } catch (_) {}
  }

  Future<void> stopBot() async {
    try {
      final result = await _ref.read(tradingServiceProvider).stopBot();
      state = result['status'] as String? ?? 'stopped';
    } catch (_) {
      state = 'stopped';
    }
  }

  void setStatus(String s) => state = s;
  void clearError() => _lastError = null;
}

final botStatusProvider = StateNotifierProvider<BotStatusNotifier, String>((ref) {
  return BotStatusNotifier(ref);
});
