import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/constants/app_constants.dart';

final botSymbolProvider =
    StateNotifierProvider<BotSymbolNotifier, String>((ref) {
  return BotSymbolNotifier();
});

class BotSymbolNotifier extends StateNotifier<String> {
  BotSymbolNotifier() : super(AppConstants.defaultBotSymbol) {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(AppConstants.botSymbolKey);
    if (saved != null && saved.isNotEmpty) {
      state = saved;
    }
  }

  Future<void> setSymbol(String symbol) async {
    state = symbol;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.botSymbolKey, symbol);
  }
}
