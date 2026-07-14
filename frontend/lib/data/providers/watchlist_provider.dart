import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/watchlist_service.dart';

/// Async provider that loads the user's watchlist from the backend.
final watchlistProvider =
    AsyncNotifierProvider<WatchlistNotifier, List<String>>(
  WatchlistNotifier.new,
);

class WatchlistNotifier extends AsyncNotifier<List<String>> {
  @override
  Future<List<String>> build() async {
    return ref.read(watchlistServiceProvider).getWatchlist();
  }

  /// Reload from server.
  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref.read(watchlistServiceProvider).getWatchlist(),
    );
  }

  /// Add a symbol and refresh.
  Future<void> add(String symbol) async {
    await ref.read(watchlistServiceProvider).addSymbol(symbol);
    await refresh();
  }

  /// Remove a symbol and refresh.
  Future<void> remove(String symbol) async {
    await ref.read(watchlistServiceProvider).removeSymbol(symbol);
    await refresh();
  }

  /// Clear all symbols and refresh.
  Future<void> clear() async {
    await ref.read(watchlistServiceProvider).clearWatchlist();
    await refresh();
  }
}
