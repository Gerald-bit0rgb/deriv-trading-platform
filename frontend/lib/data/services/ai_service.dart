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

  // granularity is nullable and omitted from the request unless explicitly
  // provided — this lets the backend fall back to the user's saved entry
  // timeframe (Strategy Settings) instead of silently overriding it with a
  // hardcoded value on every call.
  Future<AiSignalModel> getSignal(String symbol, {int? granularity}) async {
    final r = await _dio.get(
      '/ai/signal/$symbol',
      queryParameters: granularity != null ? {'granularity': granularity} : null,
    );
    return AiSignalModel.fromJson(r.data as Map<String, dynamic>);
  }

  Future<List<AiSignalModel>> getBatchSignals(
    List<String> symbols, {
    int? granularity,
  }) async {
    final r = await _dio.post(
      '/ai/signal/batch',
      data: symbols,
      queryParameters: granularity != null ? {'granularity': granularity} : null,
    );
    return (r.data as List)
        .map((e) => AiSignalModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Map<String, dynamic>> autoTrade({
    required String symbol,
    required double lotSize,
    int? granularity,
  }) async {
    final r = await _dio.post(
      '/ai/auto-trade/$symbol',
      queryParameters: {
        'lot_size': lotSize,
        if (granularity != null) 'granularity': granularity,
      },
    );
    return r.data as Map<String, dynamic>;
  }
}
