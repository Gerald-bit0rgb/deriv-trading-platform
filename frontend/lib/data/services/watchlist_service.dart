import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_client.dart';

final watchlistServiceProvider = Provider<WatchlistService>(
  (ref) => WatchlistService(ref.read(dioProvider)),
);

class WatchlistService {
  final Dio _dio;
  WatchlistService(this._dio);

  /// Fetch current watchlist symbols for the logged-in user.
  Future<List<String>> getWatchlist() async {
    final r = await _dio.get('/watchlist');
    return List<String>.from(r.data as List);
  }

  /// Add [symbol] to the watchlist.
  Future<void> addSymbol(String symbol) async {
    await _dio.post('/watchlist/$symbol');
  }

  /// Remove [symbol] from the watchlist.
  Future<void> removeSymbol(String symbol) async {
    await _dio.delete('/watchlist/$symbol');
  }

  /// Clear all symbols from the watchlist.
  Future<void> clearWatchlist() async {
    await _dio.delete('/watchlist');
  }
}
