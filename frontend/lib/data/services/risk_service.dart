import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/risk_settings_model.dart';
import 'api_client.dart';

final riskServiceProvider = Provider<RiskService>(
  (ref) => RiskService(ref.read(dioProvider)),
);

class RiskService {
  final Dio _dio;
  RiskService(this._dio);

  Future<RiskSettingsModel> getRiskSettings() async {
    final r = await _dio.get('/risk');
    return RiskSettingsModel.fromJson(r.data as Map<String, dynamic>);
  }

  Future<RiskSettingsModel> updateRiskSettings(RiskSettingsModel settings) async {
    final r = await _dio.put('/risk', data: settings.toJson());
    return RiskSettingsModel.fromJson(r.data as Map<String, dynamic>);
  }

  Future<void> emergencyStop() async {
    await _dio.post('/risk/emergency-stop');
  }

  Future<void> emergencyReset() async {
    await _dio.post('/risk/emergency-reset');
  }
}
