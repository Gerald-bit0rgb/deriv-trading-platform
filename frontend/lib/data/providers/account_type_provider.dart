import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _kAccountTypeKey = 'account_type';

final accountTypeProvider =
    StateNotifierProvider<AccountTypeNotifier, String>((ref) {
  return AccountTypeNotifier();
});

class AccountTypeNotifier extends StateNotifier<String> {
  AccountTypeNotifier() : super('demo') {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    state = prefs.getString(_kAccountTypeKey) ?? 'demo';
  }

  Future<void> setType(String type) async {
    state = type;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kAccountTypeKey, type);
  }

  bool get isDemo => state == 'demo';
  bool get isReal => state == 'real';
}
