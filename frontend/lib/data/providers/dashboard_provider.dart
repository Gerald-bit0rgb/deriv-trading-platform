import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/account_type_provider.dart';
import '../providers/bot_symbol_provider.dart';
import '../services/dashboard_service.dart';
import '../services/trading_service.dart';

final dashboardProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  return ref.read(dashboardServiceProvider).getDashboard();
});

// ── Bot status ────────────────────────────────────────────────────────────────

class BotStatusNotifier extends StateNotifier<String> {
  final Ref _ref;
  String? _lastError;

  BotStatusNotifier(this._ref) : super('stopped');

  String? get lastError => _lastError;

  void clearError() {
    _lastError = null;
  }

  Future<void> startBot() async {
    state = 'connecting';
    _lastError = null;
    try {
      // Read selected symbol and account type from providers
      final symbol = _ref.read(botSymbolProvider);
      final accountType = _ref.read(accountTypeProvider);

      final result = await _ref.read(tradingServiceProvider).startBot(
        symbol: symbol,
        accountType: accountType,
      );
      state = result['status'] as String? ?? 'stopped';
    } catch (e) {
      final msg = e.toString();
      if (msg.contains('No Deriv API token') || msg.contains('token')) {
        _lastError =
            'No Deriv token saved. Go to Profile → save your token first.';
      } else if (msg.contains('400')) {
        _lastError = 'Could not start bot. Check your Deriv token in Profile.';
      } else {
        _lastError = 'Bot error. Please try again.';
      }
      state = 'error';
    }
  }

  Future<void> pauseBot() async {
    try {
      final result = await _ref.read(tradingServiceProvider).pauseBot();
      state = result['status'] as String? ?? state;
    } catch (_) {}
  }

  Future<void> resumeBot() async {
    try {
      final result = await _ref.read(tradingServiceProvider).resumeBot();
      state = result['status'] as String? ?? state;
    } catch (_) {}
  }

  Future<void> stopBot() async {
    try {
      final result = await _ref.read(tradingServiceProvider).stopBot();
      state = result['status'] as String? ?? 'stopped';
    } catch (_) {
      state = 'stopped';
    }
    _lastError = null;
  }

  void setStatus(String s) => state = s;
}

final botStatusProvider =
    StateNotifierProvider<BotStatusNotifier, String>((ref) {
  return BotStatusNotifier(ref);
});
