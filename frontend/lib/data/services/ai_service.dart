import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/ai_signal_model.dart';
import 'api_client.dart';

final aiServiceProvider = Provider<AiService>(
  (ref) => AiService(ref.read(dioProvider)),
);

class AiService {
  final Dio _dio;
  AiService(this._dio);

  Future<AiSignalModel> getSignal(String symbol, {int granularity = 60}) async {
    final r = await _dio.get(
      '/ai/signal/$symbol',
      queryParameters: {'granularity': granularity},
    );
    return AiSignalModel.fromJson(r.data as Map<String, dynamic>);
  }

  Future<List<AiSignalModel>> getBatchSignals(
    List<String> symbols, {
    int granularity = 60,
  }) async {
    final r = await _dio.post(
      '/ai/signal/batch',
      data: symbols,
      queryParameters: {'granularity': granularity},
    );
    return (r.data as List)
        .map((e) => AiSignalModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Map<String, dynamic>> autoTrade({
    required String symbol,
    required double stake,
    required int duration,
    required String durationUnit,
    int granularity = 60,
  }) async {
    final r = await _dio.post(
      '/ai/auto-trade/$symbol',
      queryParameters: {
        'stake': stake,
        'duration': duration,
        'duration_unit': durationUnit,
        'granularity': granularity,
      },
    );
    return r.data as Map<String, dynamic>;
  }
}
