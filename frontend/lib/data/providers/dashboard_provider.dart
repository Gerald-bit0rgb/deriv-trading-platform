import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/dashboard_service.dart';
import '../services/trading_service.dart';

final dashboardProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  return ref.read(dashboardServiceProvider).getDashboard();
});

// ── Bot status ────────────────────────────────────────────────────────────────

class BotStatusNotifier extends StateNotifier<String> {
  final Ref _ref;
  BotStatusNotifier(this._ref) : super('stopped');

  Future<void> startBot() async {
    state = 'connecting';
    try {
      final result = await _ref.read(tradingServiceProvider).startBot();
      state = result['status'] as String;
    } catch (_) {
      state = 'error';
    }
  }

  Future<void> pauseBot() async {
    try {
      final result = await _ref.read(tradingServiceProvider).pauseBot();
      state = result['status'] as String;
    } catch (_) {}
  }

  Future<void> resumeBot() async {
    try {
      final result = await _ref.read(tradingServiceProvider).resumeBot();
      state = result['status'] as String;
    } catch (_) {}
  }

  Future<void> stopBot() async {
    try {
      final result = await _ref.read(tradingServiceProvider).stopBot();
      state = result['status'] as String;
    } catch (_) {
      state = 'stopped';
    }
  }

  void setStatus(String s) => state = s;
}

final botStatusProvider = StateNotifierProvider<BotStatusNotifier, String>((ref) {
  return BotStatusNotifier(ref);
});
