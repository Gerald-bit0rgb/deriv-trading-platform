import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/trade_model.dart';
import '../../../data/services/trading_service.dart';
import '../../widgets/trade/trade_card.dart';

final tradeHistoryProvider = FutureProvider.autoDispose<List<TradeModel>>((ref) {
  return ref.read(tradingServiceProvider).getTradeHistory(
    limit: AppConstants.defaultPageSize,
  );
});

final tradeSummaryProvider = FutureProvider.autoDispose<TradeSummary>((ref) {
  return ref.read(tradingServiceProvider).getTradeSummary();
});

class HistoryScreen extends ConsumerWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyAsync = ref.watch(tradeHistoryProvider);
    final summaryAsync = ref.watch(tradeSummaryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Trade History'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.invalidate(tradeHistoryProvider);
              ref.invalidate(tradeSummaryProvider);
            },
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ── Summary cards ─────────────────────────────────────────────────
          summaryAsync.when(
            loading: () => const SizedBox(height: 80,
                child: Center(child: CircularProgressIndicator(color: AppColors.primary))),
            error: (e, _) => const SizedBox.shrink(),
            data: (s) => _SummaryGrid(summary: s),
          ),
          const SizedBox(height: 20),

          // ── Trade list ────────────────────────────────────────────────────
          Text('Recent Trades',
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),

          historyAsync.when(
            loading: () => const Center(
              child: Padding(
                padding: EdgeInsets.all(32),
                child: CircularProgressIndicator(color: AppColors.primary),
              ),
            ),
            error: (e, _) => Center(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text('Error: $e',
                    style: const TextStyle(color: AppColors.danger)),
              ),
            ),
            data: (trades) => trades.isEmpty
                ? const Center(
                    child: Padding(
                      padding: EdgeInsets.all(32),
                      child: Column(
                        children: [
                          Icon(Icons.history, size: 48, color: AppColors.textMuted),
                          SizedBox(height: 12),
                          Text('No trade history yet',
                              style: TextStyle(color: AppColors.textMuted)),
                        ],
                      ),
                    ),
                  )
                : Column(
                    children: trades.map((t) => TradeCard(trade: t)).toList(),
                  ),
          ),
        ],
      ),
    );
  }
}

class _SummaryGrid extends StatelessWidget {
  final TradeSummary summary;
  const _SummaryGrid({required this.summary});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // P/L highlight
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: summary.totalProfit >= 0
                  ? [AppColors.success.withOpacity(0.8), AppColors.success]
                  : [AppColors.danger.withOpacity(0.8), AppColors.danger],
            ),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(
            children: [
              const Text('Total Profit / Loss',
                  style: TextStyle(color: Colors.white70, fontSize: 13)),
              const SizedBox(height: 4),
              Text(
                Fmt.signedMoney(summary.totalProfit),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            _StatBadge(label: 'Total', value: '${summary.totalTrades}',
                icon: Icons.bar_chart, color: AppColors.primary),
            const SizedBox(width: 8),
            _StatBadge(label: 'Win Rate', value: Fmt.pct(summary.winRate),
                icon: Icons.emoji_events_outlined, color: AppColors.success),
            const SizedBox(width: 8),
            _StatBadge(label: 'Today P/L', value: Fmt.signedMoney(summary.todayProfit),
                icon: Icons.today,
                color: summary.todayProfit >= 0 ? AppColors.success : AppColors.danger),
          ],
        ),
      ],
    );
  }
}

class _StatBadge extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  const _StatBadge({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isDark ? AppColors.darkCard : AppColors.lightCard,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 18),
            const SizedBox(height: 4),
            Text(value,
                style: TextStyle(
                    fontWeight: FontWeight.w700, color: color, fontSize: 14)),
            Text(label,
                style: const TextStyle(color: AppColors.textMuted, fontSize: 10)),
          ],
        ),
      ),
    );
  }
}
