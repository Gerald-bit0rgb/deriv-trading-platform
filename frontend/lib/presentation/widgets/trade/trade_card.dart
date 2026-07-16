import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/models/trade_model.dart';

class TradeCard extends StatelessWidget {
  final TradeModel trade;
  final VoidCallback? onClose;

  const TradeCard({
    super.key,
    required this.trade,
    this.onClose,
  });

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

  Widget _stat(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: AppColors.textMuted,
            fontSize: 11,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            color: AppColors.textDefault,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surfaceSecondary,
        borderRadius: BorderRadius.circular(12),
        border: Border(
          left: BorderSide(color: _directionColor, width: 3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: Direction + Status
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                _directionLabel,
                style: TextStyle(
                  color: _directionColor,
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
              Row(
                children: [
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: _resultColor.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      _resultLabel,
                      style: TextStyle(
                        color: _resultColor,
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  if (onClose != null) ...[
                    const SizedBox(width: 8),
                    GestureDetector(
                      onTap: onClose,
                      child: const Icon(Icons.close,
                          size: 18, color: AppColors.textMuted),
                    ),
                  ],
                ],
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Symbol
          Text(
            trade.symbol,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),

          // Stats Grid: Lot Size, Entry/Exit Price, Profit
          GridView(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.2,
            ),
            children: [
              _stat('Lot Size', trade.lotSize.toStringAsFixed(2)),
              if (trade.entryPrice != null)
                _stat('Entry', '\$${trade.entryPrice!.toStringAsFixed(5)}')
              else
                _stat('Entry', '—'),
              if (trade.exitPrice != null)
                _stat('Exit', '\$${trade.exitPrice!.toStringAsFixed(5)}')
              else
                _stat('Exit', '—'),
              if (trade.profit != null)
                _stat(
                  'P&L',
                  '\$${trade.profit!.toStringAsFixed(2)}',
                )
              else
                _stat('P&L', '—'),
            ],
          ),

          // AI Signal (if available)
          if (trade.aiSignal != null) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(Icons.bolt, size: 14, color: AppColors.accent),
                const SizedBox(width: 6),
                Text(
                  'AI: ${trade.aiSignal!.toUpperCase()}',
                  style: TextStyle(
                    color: trade.aiSignal == 'BUY'
                        ? AppColors.buyColor
                        : AppColors.sellColor,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                if (trade.aiConfidence != null)
                  Text(
                    ' (${(trade.aiConfidence! * 100).toStringAsFixed(0)}%)',
                    style: const TextStyle(
                      color: AppColors.textMuted,
                      fontSize: 11,
                    ),
                  ),
              ],
            ),
          ],

          // Timestamp
          if (trade.openedAt != null)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Text(
                _formatTime(trade.openedAt!),
                style: const TextStyle(
                  color: AppColors.textMuted,
                  fontSize: 11,
                ),
              ),
            ),
        ],
      ),
    );
  }

  String _formatTime(DateTime dt) {
    return '${dt.day} ${_monthName(dt.month)} ${dt.year} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }

  String _monthName(int m) => [
        'Jan',
        'Feb',
        'Mar',
        'Apr',
        'May',
        'Jun',
        'Jul',
        'Aug',
        'Sep',
        'Oct',
        'Nov',
        'Dec'
      ][m - 1];
}
