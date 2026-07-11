import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/trade_model.dart';

class TradeCard extends StatelessWidget {
  final TradeModel trade;
  final VoidCallback? onClose;

  const TradeCard({super.key, required this.trade, this.onClose});

  Color get _statusColor {
    if (trade.status == 'open') return AppColors.info;
    if (trade.isWin == true) return AppColors.success;
    return AppColors.danger;
  }

  Color get _contractColor =>
      trade.contractType == 'CALL' ? AppColors.buyColor : AppColors.sellColor;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : AppColors.lightCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Header row ───────────────────────────────────────────────────
          Row(
            children: [
              // Contract type badge
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: _contractColor.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  trade.contractType,
                  style: TextStyle(
                    color: _contractColor,
                    fontWeight: FontWeight.w700,
                    fontSize: 12,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              // Symbol
              Text(
                trade.symbol,
                style: theme.textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              const Spacer(),
              // Status badge
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _statusColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  trade.status.toUpperCase(),
                  style: TextStyle(
                    color: _statusColor,
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // ── Stats row ─────────────────────────────────────────────────────
          Row(
            children: [
              _stat('Stake', Fmt.money(trade.stake)),
              _stat('Payout', Fmt.money(trade.payout)),
              _stat(
                'P/L',
                trade.profit != null ? Fmt.signedMoney(trade.profit) : '—',
                valueColor: trade.profit != null
                    ? (trade.profit! >= 0 ? AppColors.success : AppColors.danger)
                    : null,
              ),
            ],
          ),

          // ── AI signal (if any) ────────────────────────────────────────────
          if (trade.aiSignal != null) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.auto_awesome, size: 14, color: AppColors.accent),
                const SizedBox(width: 4),
                Text(
                  'AI: ${trade.aiSignal} (${Fmt.confidence(trade.aiConfidence ?? 0)})',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: AppColors.accent,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ],

          // ── Time + close button ────────────────────────────────────────────
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                Fmt.datetime(trade.openedAt),
                style: theme.textTheme.bodySmall?.copyWith(
                  color: AppColors.textMuted,
                ),
              ),
              if (trade.status == 'open' && onClose != null)
                TextButton.icon(
                  onPressed: onClose,
                  icon: const Icon(Icons.close, size: 14),
                  label: const Text('Close'),
                  style: TextButton.styleFrom(
                    foregroundColor: AppColors.danger,
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    minimumSize: Size.zero,
                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                ),
            ],
          ),
        ],
      ),
    ).animate().fadeIn(duration: 300.ms).slideY(begin: 0.05);
  }

  Widget _stat(String label, String value, {Color? valueColor}) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label,
              style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
          const SizedBox(height: 2),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 13,
              color: valueColor,
            ),
          ),
        ],
      ),
    );
  }
}
