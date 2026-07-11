import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/trade_model.dart';
import 'api_client.dart';

final tradingServiceProvider = Provider<TradingService>(
  (ref) => TradingService(ref.read(dioProvider)),
);

class TradingService {
  final Dio _dio;
  TradingService(this._dio);

  // ── Bot control ────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> startBot() async {
    final r = await _dio.post('/trading/start');
    return r.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> pauseBot() async {
    final r = await _dio.post('/trading/pause');
    return r.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> resumeBot() async {
    final r = await _dio.post('/trading/resume');
    return r.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> stopBot() async {
    final r = await _dio.post('/trading/stop');
    return r.data as Map<String, dynamic>;
  }

  Future<String> getBotStatus() async {
    final r = await _dio.get('/trading/status');
    return (r.data as Map<String, dynamic>)['status'] as String;
  }

  // ── Balance ────────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getBalance() async {
    final r = await _dio.get('/trading/balance');
    return r.data as Map<String, dynamic>;
  }

  // ── Trades ─────────────────────────────────────────────────────────────────
  Future<TradeModel> placeTrade({
    required String symbol,
    required String contractType,
    required double stake,
    required int duration,
    required String durationUnit,
  }) async {
    final r = await _dio.post('/trading/trade', data: {
      'symbol': symbol,
      'contract_type': contractType,
      'stake': stake,
      'duration': duration,
      'duration_unit': durationUnit,
    });
    return TradeModel.fromJson(r.data as Map<String, dynamic>);
  }

  Future<TradeModel> closeTrade(int tradeId) async {
    final r = await _dio.delete('/trading/trade/$tradeId');
    return TradeModel.fromJson(r.data as Map<String, dynamic>);
  }

  Future<List<TradeModel>> getOpenTrades() async {
    final r = await _dio.get('/trading/trades/open');
    return (r.data as List)
        .map((e) => TradeModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<TradeModel>> getTradeHistory({
    int limit = 20,
    int offset = 0,
  }) async {
    final r = await _dio.get('/trading/trades', queryParameters: {
      'limit': limit,
      'offset': offset,
    });
    return (r.data as List)
        .map((e) => TradeModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<TradeSummary> getTradeSummary() async {
    final r = await _dio.get('/trading/summary');
    return TradeSummary.fromJson(r.data as Map<String, dynamic>);
  }
}
