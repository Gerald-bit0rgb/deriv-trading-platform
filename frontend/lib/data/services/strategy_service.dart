import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/strategy_settings_model.dart';
import 'api_client.dart';

final strategyServiceProvider = Provider<StrategyService>(
  (ref) => StrategyService(ref.read(dioProvider)),
);

class StrategyService {
  final Dio _dio;
  StrategyService(this._dio);

  Future<StrategySettingsModel> getSettings() async {
    final r = await _dio.get('/strategy');
    return StrategySettingsModel.fromJson(r.data as Map<String, dynamic>);
  }

  Future<StrategySettingsModel> updateSettings(StrategySettingsModel s) async {
    final r = await _dio.put('/strategy', data: s.toJson());
    return StrategySettingsModel.fromJson(r.data as Map<String, dynamic>);
  }

  Future<StrategySettingsModel> resetSettings() async {
    final r = await _dio.post('/strategy/reset');
    return StrategySettingsModel.fromJson(r.data as Map<String, dynamic>);
  }
}
