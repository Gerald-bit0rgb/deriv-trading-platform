import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../../../data/providers/watchlist_provider.dart';

// ─────────────────────────────────────────────────────────────────────────────
// All symbols the bot supports, grouped by category.
// These match _ALLOWED_SYMBOLS in the backend watchlist route.
// ─────────────────────────────────────────────────────────────────────────────
const _symbolGroups = <String, List<String>>{
  'Volatility Indices': [
    'R_10', 'R_25', 'R_50', 'R_75', 'R_100',
  ],
  'Volatility (1s)': [
    '1HZ10V', '1HZ25V', '1HZ50V', '1HZ75V', '1HZ100V',
  ],
  'Jump Indices': [
    'JD10', 'JD25', 'JD50', 'JD75', 'JD100',
  ],
  'Forex / Commodities': [
    'frxEURUSD', 'frxGBPUSD', 'frxUSDJPY', 'frxAUDUSD', 'frxUSDCAD', 'frxXAUUSD',
  ],
};

// Human-friendly display names.
const _symbolLabels = <String, String>{
  'R_10':       'Vol 10 Index',
  'R_25':       'Vol 25 Index',
  'R_50':       'Vol 50 Index',
  'R_75':       'Vol 75 Index',
  'R_100':      'Vol 100 Index',
  '1HZ10V':     'Vol 10 (1s)',
  '1HZ25V':     'Vol 25 (1s)',
  '1HZ50V':     'Vol 50 (1s)',
  '1HZ75V':     'Vol 75 (1s)',
  '1HZ100V':    'Vol 100 (1s)',
  'JD10':       'Jump 10 Index',
  'JD25':       'Jump 25 Index',
  'JD50':       'Jump 50 Index',
  'JD75':       'Jump 75 Index',
  'JD100':      'Jump 100 Index',
  'frxEURUSD':  'EUR/USD',
  'frxGBPUSD':  'GBP/USD',
  'frxUSDJPY':  'USD/JPY',
  'frxAUDUSD':  'AUD/USD',
  'frxUSDCAD':  'USD/CAD',
  'frxXAUUSD':  'Gold/USD',
};

String _label(String sym) => _symbolLabels[sym] ?? sym;

// ─────────────────────────────────────────────────────────────────────────────

class WatchlistScreen extends ConsumerWidget {
  const WatchlistScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final watchlistAsync = ref.watch(watchlistProvider);

    return Scaffold(
      backgroundColor: AppColors.darkBg,
      appBar: AppBar(
        backgroundColor: AppColors.darkCard,
        title: const Text(
          'Watchlist',
          style: TextStyle(color: AppColors.textLight, fontWeight: FontWeight.bold),
        ),
        actions: [
          // Clear all button
          watchlistAsync.when(
            data: (list) => list.isEmpty
                ? const SizedBox.shrink()
                : IconButton(
                    icon: const Icon(Icons.delete_sweep_rounded,
                        color: AppColors.danger),
                    tooltip: 'Clear watchlist',
                    onPressed: () => _confirmClear(context, ref),
                  ),
            loading: () => const SizedBox.shrink(),
            error:   (_, __) => const SizedBox.shrink(),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: AppColors.accent),
            tooltip: 'Refresh',
            onPressed: () => ref.read(watchlistProvider.notifier).refresh(),
          ),
        ],
      ),
      body: watchlistAsync.when(
        loading: () => const Center(
          child: CircularProgressIndicator(color: AppColors.accent),
        ),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, color: AppColors.danger, size: 48),
              const SizedBox(height: 12),
              Text('Failed to load watchlist',
                  style: const TextStyle(color: AppColors.textLight)),
              const SizedBox(height: 8),
              Text('$e',
                  style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                  textAlign: TextAlign.center),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () =>
                    ref.read(watchlistProvider.notifier).refresh(),
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
                style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary),
              ),
            ],
          ),
        ),
        data: (watchlist) => _WatchlistBody(watchlist: watchlist),
      ),
      // FAB opens the "add symbols" bottom sheet
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showAddSymbolSheet(context, ref),
        backgroundColor: AppColors.primary,
        icon: const Icon(Icons.add),
        label: const Text('Add Symbol'),
      ),
    );
  }

  // ── Confirm clear dialog ───────────────────────────────────────────────────
  Future<void> _confirmClear(BuildContext context, WidgetRef ref) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.darkCard,
        title: const Text('Clear Watchlist',
            style: TextStyle(color: AppColors.textLight)),
        content: const Text(
          'Remove all symbols? The bot will fall back to default symbols (R_100, R_75, R_50).',
          style: TextStyle(color: AppColors.textMuted),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger),
            child: const Text('Clear All'),
          ),
        ],
      ),
    );
    if (ok == true) {
      await ref.read(watchlistProvider.notifier).clear();
    }
  }

  // ── Bottom sheet: pick symbols to add ─────────────────────────────────────
  void _showAddSymbolSheet(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.darkCard,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _AddSymbolSheet(ref: ref),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Body — current watchlist
// ─────────────────────────────────────────────────────────────────────────────
class _WatchlistBody extends ConsumerWidget {
  final List<String> watchlist;
  const _WatchlistBody({required this.watchlist});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (watchlist.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.playlist_add_check_rounded,
                color: AppColors.textMuted, size: 72),
            const SizedBox(height: 16),
            const Text(
              'No symbols in your watchlist',
              style: TextStyle(
                  color: AppColors.textLight,
                  fontSize: 18,
                  fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            const Text(
              'Bot will use R_100 · R_75 · R_50 as defaults.\nTap + Add Symbol to customise.',
              style: TextStyle(color: AppColors.textMuted, fontSize: 13),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Info banner
        Container(
          margin: const EdgeInsets.fromLTRB(16, 16, 16, 0),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: AppColors.primary.withOpacity(0.12),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.primary.withOpacity(0.3)),
          ),
          child: Row(
            children: [
              const Icon(Icons.info_outline_rounded,
                  color: AppColors.primary, size: 18),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Bot scans all ${watchlist.length} symbol(s) on every new bar '
                  'and trades any that meet your confidence threshold.',
                  style: const TextStyle(
                      color: AppColors.textLight, fontSize: 12),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),

        // List
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
            itemCount: watchlist.length,
            itemBuilder: (context, i) {
              final sym = watchlist[i];
              return _WatchlistTile(
                symbol: sym,
                index: i + 1,
                onRemove: () =>
                    ref.read(watchlistProvider.notifier).remove(sym),
              );
            },
          ),
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Single watchlist tile
// ─────────────────────────────────────────────────────────────────────────────
class _WatchlistTile extends StatelessWidget {
  final String symbol;
  final int index;
  final VoidCallback onRemove;

  const _WatchlistTile({
    required this.symbol,
    required this.index,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: AppColors.darkCardLight,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.darkBorder),
      ),
      child: ListTile(
        leading: CircleAvatar(
          radius: 18,
          backgroundColor: AppColors.primary.withOpacity(0.2),
          child: Text(
            '$index',
            style: const TextStyle(
                color: AppColors.primary,
                fontWeight: FontWeight.bold,
                fontSize: 13),
          ),
        ),
        title: Text(
          _label(symbol),
          style: const TextStyle(
              color: AppColors.textLight, fontWeight: FontWeight.w600),
        ),
        subtitle: Text(
          symbol,
          style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
        ),
        trailing: IconButton(
          icon: const Icon(Icons.remove_circle_outline_rounded,
              color: AppColors.danger),
          tooltip: 'Remove from watchlist',
          onPressed: onRemove,
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Bottom sheet — browse all available symbols and add
// ─────────────────────────────────────────────────────────────────────────────
class _AddSymbolSheet extends ConsumerStatefulWidget {
  final WidgetRef ref;
  const _AddSymbolSheet({required this.ref});

  @override
  ConsumerState<_AddSymbolSheet> createState() => _AddSymbolSheetState();
}

class _AddSymbolSheetState extends ConsumerState<_AddSymbolSheet> {
  String _search = '';
  final _searchCtrl = TextEditingController();

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final watchlist = ref.watch(watchlistProvider).valueOrNull ?? [];

    // Filter all symbols by search query
    final query = _search.toLowerCase();
    final filtered = _symbolGroups.entries
        .map((entry) {
          final matches = entry.value.where((sym) =>
              sym.toLowerCase().contains(query) ||
              _label(sym).toLowerCase().contains(query));
          return MapEntry(entry.key, matches.toList());
        })
        .where((e) => e.value.isNotEmpty)
        .toList();

    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.75,
      maxChildSize: 0.95,
      minChildSize: 0.4,
      builder: (_, scrollCtrl) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: Column(
          children: [
            // Handle
            Container(
              margin: const EdgeInsets.symmetric(vertical: 10),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.darkBorder,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const Text(
              'Add Symbol',
              style: TextStyle(
                  color: AppColors.textLight,
                  fontSize: 18,
                  fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),

            // Search bar
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: TextField(
                controller: _searchCtrl,
                style: const TextStyle(color: AppColors.textLight),
                decoration: InputDecoration(
                  hintText: 'Search symbols…',
                  hintStyle:
                      const TextStyle(color: AppColors.textMuted),
                  prefixIcon: const Icon(Icons.search,
                      color: AppColors.textMuted),
                  suffixIcon: _search.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear,
                              color: AppColors.textMuted),
                          onPressed: () {
                            _searchCtrl.clear();
                            setState(() => _search = '');
                          },
                        )
                      : null,
                  filled: true,
                  fillColor: AppColors.darkCardLight,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: BorderSide.none,
                  ),
                ),
                onChanged: (v) => setState(() => _search = v),
              ),
            ),
            const SizedBox(height: 10),

            // Symbol list
            Expanded(
              child: filtered.isEmpty
                  ? const Center(
                      child: Text('No symbols match',
                          style: TextStyle(color: AppColors.textMuted)),
                    )
                  : ListView(
                      controller: scrollCtrl,
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                      children: [
                        for (final group in filtered) ...[
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            child: Text(
                              group.key,
                              style: const TextStyle(
                                color: AppColors.accent,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                          ),
                          for (final sym in group.value)
                            _AddSymbolTile(
                              symbol: sym,
                              isAdded: watchlist.contains(sym),
                              onTap: () async {
                                if (watchlist.contains(sym)) {
                                  await widget.ref
                                      .read(watchlistProvider.notifier)
                                      .remove(sym);
                                } else {
                                  await widget.ref
                                      .read(watchlistProvider.notifier)
                                      .add(sym);
                                }
                              },
                            ),
                        ],
                      ],
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Tile inside the add-symbol sheet
// ─────────────────────────────────────────────────────────────────────────────
class _AddSymbolTile extends StatelessWidget {
  final String symbol;
  final bool isAdded;
  final VoidCallback onTap;

  const _AddSymbolTile({
    required this.symbol,
    required this.isAdded,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: isAdded
            ? AppColors.primary.withOpacity(0.15)
            : AppColors.darkCardLight,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isAdded
              ? AppColors.primary.withOpacity(0.4)
              : AppColors.darkBorder,
        ),
      ),
      child: ListTile(
        dense: true,
        title: Text(
          _label(symbol),
          style: TextStyle(
            color: isAdded ? AppColors.primary : AppColors.textLight,
            fontWeight: FontWeight.w600,
          ),
        ),
        subtitle: Text(
          symbol,
          style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
        ),
        trailing: isAdded
            ? const Icon(Icons.check_circle_rounded, color: AppColors.primary)
            : const Icon(Icons.add_circle_outline_rounded,
                color: AppColors.textMuted),
        onTap: onTap,
      ),
    );
  }
}
