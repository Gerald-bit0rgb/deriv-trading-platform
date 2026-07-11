import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/models/trade_model.dart';
import '../../../data/providers/auth_provider.dart';
import '../../../data/services/trading_service.dart';
import '../../widgets/trade/trade_card.dart';

// ── Providers ──────────────────────────────────────────────────────────────
final openTradesProvider = FutureProvider.autoDispose<List<TradeModel>>((ref) {
  return ref.read(tradingServiceProvider).getOpenTrades();
});

class TradingScreen extends ConsumerStatefulWidget {
  const TradingScreen({super.key});

  @override
  ConsumerState<TradingScreen> createState() => _TradingScreenState();
}

class _TradingScreenState extends ConsumerState<TradingScreen> {
  final _formKey = GlobalKey<FormState>();
  String _symbol = AppConstants.popularSymbols.first;
  String _contractType = 'CALL';
  double _stake = 1.0;
  int _duration = 5;
  String _durationUnit = 't';
  bool _isSubmitting = false;

  Future<void> _placeTrade() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isSubmitting = true);
    try {
      await ref.read(tradingServiceProvider).placeTrade(
            symbol: _symbol,
            contractType: _contractType,
            stake: _stake,
            duration: _duration,
            durationUnit: _durationUnit,
          );
      ref.invalidate(openTradesProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Trade placed successfully!'),
            backgroundColor: AppColors.success,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: ${e.toString()}'),
            backgroundColor: AppColors.danger,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  Future<void> _closeTrade(int tradeId) async {
    try {
      await ref.read(tradingServiceProvider).closeTrade(tradeId);
      ref.invalidate(openTradesProvider);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Close failed: $e'), backgroundColor: AppColors.danger),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final openAsync = ref.watch(openTradesProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Trading')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ── Place Trade form ───────────────────────────────────────────────
          _SectionHeader(title: 'Place Manual Trade'),
          const SizedBox(height: 8),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  children: [
                    // Symbol picker
                    DropdownButtonFormField<String>(
                      value: _symbol,
                      decoration: const InputDecoration(
                        labelText: 'Symbol',
                        prefixIcon: Icon(Icons.show_chart),
                      ),
                      items: AppConstants.popularSymbols
                          .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                          .toList(),
                      onChanged: (v) => setState(() => _symbol = v!),
                    ),
                    const SizedBox(height: 12),

                    // Contract type
                    Row(
                      children: AppConstants.contractTypes.map((type) {
                        final selected = _contractType == type;
                        final color = type == 'CALL' ? AppColors.buyColor : AppColors.sellColor;
                        return Expanded(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 4),
                            child: GestureDetector(
                              onTap: () => setState(() => _contractType = type),
                              child: Container(
                                padding: const EdgeInsets.symmetric(vertical: 12),
                                decoration: BoxDecoration(
                                  color: selected ? color : color.withOpacity(0.08),
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(color: color),
                                ),
                                child: Center(
                                  child: Text(
                                    type == 'CALL' ? '▲ CALL (Rise)' : '▼ PUT (Fall)',
                                    style: TextStyle(
                                      color: selected ? Colors.white : color,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 12),

                    // Stake
                    TextFormField(
                      initialValue: _stake.toString(),
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      decoration: const InputDecoration(
                        labelText: 'Stake (USD)',
                        prefixIcon: Icon(Icons.attach_money),
                      ),
                      onChanged: (v) => _stake = double.tryParse(v) ?? 1.0,
                      validator: (v) {
                        final n = double.tryParse(v ?? '');
                        if (n == null || n <= 0) return 'Enter a valid stake';
                        return null;
                      },
                    ),
                    const SizedBox(height: 12),

                    // Duration
                    Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: TextFormField(
                            initialValue: _duration.toString(),
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(labelText: 'Duration'),
                            onChanged: (v) => _duration = int.tryParse(v) ?? 5,
                            validator: (v) {
                              final n = int.tryParse(v ?? '');
                              if (n == null || n <= 0) return 'Enter duration';
                              return null;
                            },
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          flex: 3,
                          child: DropdownButtonFormField<String>(
                            value: _durationUnit,
                            decoration: const InputDecoration(labelText: 'Unit'),
                            items: AppConstants.durationUnits
                                .map((u) => DropdownMenuItem(
                                      value: u['value'] as String,
                                      child: Text(u['label'] as String),
                                    ))
                                .toList(),
                            onChanged: (v) => setState(() => _durationUnit = v!),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),

                    ElevatedButton(
                      onPressed: _isSubmitting ? null : _placeTrade,
                      child: _isSubmitting
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(
                                color: Colors.white,
                                strokeWidth: 2,
                              ),
                            )
                          : Text(
                              '${_contractType == 'CALL' ? '▲ BUY CALL' : '▼ BUY PUT'} — Stake \$$_stake',
                            ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(height: 24),

          // ── Open trades ────────────────────────────────────────────────────
          _SectionHeader(
            title: 'Open Trades',
            action: TextButton(
              onPressed: () => ref.invalidate(openTradesProvider),
              child: const Text('Refresh'),
            ),
          ),
          const SizedBox(height: 8),
          openAsync.when(
            loading: () => const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: CircularProgressIndicator(color: AppColors.primary),
              ),
            ),
            error: (e, _) => Text('Error: $e',
                style: const TextStyle(color: AppColors.danger)),
            data: (trades) => trades.isEmpty
                ? const _EmptyState(message: 'No open trades')
                : Column(
                    children: trades
                        .map((t) => TradeCard(
                              trade: t,
                              onClose: () => _closeTrade(t.id),
                            ))
                        .toList(),
                  ),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final Widget? action;
  const _SectionHeader({required this.title, this.action});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(title,
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.w700)),
        if (action != null) action!,
      ],
    );
  }
}

class _EmptyState extends StatelessWidget {
  final String message;
  const _EmptyState({required this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          children: [
            const Icon(Icons.inbox_outlined, size: 48, color: AppColors.textMuted),
            const SizedBox(height: 12),
            Text(message,
                style: const TextStyle(color: AppColors.textMuted)),
          ],
        ),
      ),
    );
  }
}
