import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/trade_model.dart';
import '../../../data/services/trading_service.dart';

// ── Providers ──────────────────────────────────────────────────────────────

final tradeHistoryProvider =
    FutureProvider.autoDispose<List<TradeModel>>((ref) {
  return ref.read(tradingServiceProvider).getTradeHistory(limit: 100);
});

final tradeSummaryProvider =
    FutureProvider.autoDispose<TradeSummary>((ref) {
  return ref.read(tradingServiceProvider).getTradeSummary();
});

// ── Screen ─────────────────────────────────────────────────────────────────

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
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(tradeHistoryProvider);
          ref.invalidate(tradeSummaryProvider);
        },
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // ── Summary ─────────────────────────────────────────────────────
            summaryAsync.when(
              loading: () => const SizedBox(
                height: 80,
                child: Center(
                    child: CircularProgressIndicator(
                        color: AppColors.primary)),
              ),
              error: (e, _) => const SizedBox.shrink(),
              data: (s) => _SummarySection(summary: s),
            ),

            const SizedBox(height: 20),

            // ── Trade list ───────────────────────────────────────────────────
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'All Trades',
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
                historyAsync.when(
                  loading: () => const SizedBox.shrink(),
                  error: (_, __) => const SizedBox.shrink(),
                  data: (trades) => Text(
                    '${trades.length} trades',
                    style: const TextStyle(
                        color: AppColors.textMuted, fontSize: 12),
                  ),
                ),
              ],
            ),
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
                  child: Column(
                    children: [
                      const Icon(Icons.error_outline,
                          size: 40, color: AppColors.danger),
                      const SizedBox(height: 8),
                      Text('Error loading trades',
                          style: const TextStyle(color: AppColors.danger)),
                    ],
                  ),
                ),
              ),
              data: (trades) => trades.isEmpty
                  ? const _EmptyHistory()
                  : Column(
                      children: trades
                          .map((t) => _TradeHistoryCard(trade: t))
                          .toList(),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Empty state ─────────────────────────────────────────────────────────────

class _EmptyHistory extends StatelessWidget {
  const _EmptyHistory();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(48),
        child: Column(
          children: [
            const Icon(Icons.history, size: 64, color: AppColors.textMuted),
            const SizedBox(height: 16),
            const Text(
              'No trades yet',
              style: TextStyle(
                  color: AppColors.textMuted,
                  fontSize: 18,
                  fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            const Text(
              'Start the bot or place a trade manually.\nAll trades will appear here.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textMuted, fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Summary section ─────────────────────────────────────────────────────────

class _SummarySection extends StatelessWidget {
  final TradeSummary summary;
  const _SummarySection({required this.summary});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Total P/L banner
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: summary.totalProfit >= 0
                  ? [const Color(0xFF1a7a4a), AppColors.success]
                  : [const Color(0xFF7a1a1a), AppColors.danger],
            ),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Total Profit / Loss',
                      style:
                          TextStyle(color: Colors.white70, fontSize: 12)),
                  const SizedBox(height: 4),
                  Text(
                    Fmt.signedMoney(summary.totalProfit),
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 26,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${summary.totalTrades} trades',
                    style: const TextStyle(
                        color: Colors.white70, fontSize: 13),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Win rate ${Fmt.pct(summary.winRate)}',
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        fontWeight: FontWeight.w700),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 10),
        // Today row
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Theme.of(context).brightness == Brightness.dark
                ? AppColors.darkCard
                : AppColors.lightCard,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: Theme.of(context).brightness == Brightness.dark
                  ? AppColors.darkBorder
                  : AppColors.lightBorder,
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _MiniStat(
                  label: "Today's P/L",
                  value: Fmt.signedMoney(summary.todayProfit),
                  color: summary.todayProfit >= 0
                      ? AppColors.success
                      : AppColors.danger),
              _MiniStat(
                  label: 'Today trades',
                  value: '${summary.todayTrades}',
                  color: AppColors.info),
              _MiniStat(
                  label: 'Open now',
                  value: '${summary.openTrades}',
                  color: AppColors.warning),
            ],
          ),
        ),
      ],
    );
  }
}

class _MiniStat extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _MiniStat(
      {required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value,
            style: TextStyle(
                color: color,
                fontWeight: FontWeight.w700,
                fontSize: 16)),
        const SizedBox(height: 2),
        Text(label,
            style:
                const TextStyle(color: AppColors.textMuted, fontSize: 11)),
      ],
    );
  }
}

// ── Trade history card ───────────────────────────────────────────────────────

class _TradeHistoryCard extends StatelessWidget {
  final TradeModel trade;
  const _TradeHistoryCard({required this.trade});

  Color get _directionColor =>
      trade.isBuy ? AppColors.buyColor : AppColors.sellColor;

  Color get _resultColor {
    if (trade.status == 'open') return AppColors.info;
    return (trade.isWin ?? false) ? AppColors.success : AppColors.danger;
  }

  String get _resultLabel {
    if (trade.status == 'open') return 'OPEN';
    return (trade.isWin ?? false) ? 'WIN' : 'LOSS';
  }

  String get _directionLabel => trade.isBuy ? '▲ BUY' : '▼ SELL';

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : AppColors.lightCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: _resultColor.withOpacity(0.25),
          width: 1.5,
        ),
      ),
      child: Column(
        children: [
          // ── Top row: direction + symbol + result ──────────────────────────
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: _resultColor.withOpacity(0.06),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(11),
                topRight: Radius.circular(11),
              ),
            ),
            child: Row(
              children: [
                // Direction badge
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: _directionColor.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    _directionLabel,
                    style: TextStyle(
                      color: _directionColor,
                      fontWeight: FontWeight.w800,
                      fontSize: 13,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                // Symbol
                Text(
                  trade.symbol,
                  style: const TextStyle(
                      fontWeight: FontWeight.w700, fontSize: 14),
                ),
                const Spacer(),
                // Result badge
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: _resultColor.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    _resultLabel,
                    style: TextStyle(
                      color: _resultColor,
                      fontWeight: FontWeight.w800,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // ── Details rows ──────────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            child: Column(
              children: [
                // Date and time
                _DetailRow(
                  icon: Icons.calendar_today_outlined,
                  label: 'Date',
                  value: trade.openedAt != null
                      ? Fmt.date(trade.openedAt)
                      : '—',
                ),
                const SizedBox(height: 6),
                _DetailRow(
                  icon: Icons.access_time,
                  label: 'Open time',
                  value: trade.openedAt != null
                      ? Fmt.time(trade.openedAt)
                      : '—',
                ),
                if (trade.closedAt != null) ...[
                  const SizedBox(height: 6),
                  _DetailRow(
                    icon: Icons.timer_off_outlined,
                    label: 'Close time',
                    value: Fmt.time(trade.closedAt),
                  ),
                ],
                const SizedBox(height: 6),
                // Lot size and profit on same row
                Row(
                  children: [
                    Expanded(
                      child: _DetailRow(
                        icon: Icons.attach_money,
                        label: 'Stake',
                        value: '\$${trade.lotSize.toStringAsFixed(2)}',
                      ),
                    ),
                    Expanded(
                      child: _DetailRow(
                        icon: trade.profit != null && trade.profit! >= 0
                            ? Icons.trending_up
                            : Icons.trending_down,
                        label: 'P/L',
                        value: trade.profit != null
                            ? Fmt.signedMoney(trade.profit)
                            : '—',
                        valueColor: trade.profit != null
                            ? (trade.profit! >= 0
                                ? AppColors.success
                                : AppColors.danger)
                            : null,
                      ),
                    ),
                  ],
                ),
                // AI signal if present
                if (trade.aiSignal != null) ...[
                  const SizedBox(height: 6),
                  _DetailRow(
                    icon: Icons.auto_awesome,
                    label: 'AI Signal',
                    value:
                        '${trade.aiSignal} (${((trade.aiConfidence ?? 0) * 100).toStringAsFixed(0)}%)',
                    valueColor: AppColors.accent,
                  ),
                ],
                // Source
                const SizedBox(height: 6),
                _DetailRow(
                  icon: trade.source == 'auto'
                      ? Icons.smart_toy_outlined
                      : Icons.touch_app_outlined,
                  label: 'Source',
                  value: trade.source == 'auto'
                      ? 'Bot (auto)'
                      : trade.source == 'ai'
                          ? 'AI Execute'
                          : 'Manual',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color? valueColor;

  const _DetailRow({
    required this.icon,
    required this.label,
    required this.value,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 13, color: AppColors.textMuted),
        const SizedBox(width: 5),
        Text(
          '$label: ',
          style: const TextStyle(
              color: AppColors.textMuted,
              fontSize: 12,
              fontWeight: FontWeight.w500),
        ),
        Flexible(
          child: Text(
            value,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: valueColor,
            ),
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}
