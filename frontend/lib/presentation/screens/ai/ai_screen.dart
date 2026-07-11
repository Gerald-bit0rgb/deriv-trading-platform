import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/ai_signal_model.dart';
import '../../../data/services/ai_service.dart';

class AiScreen extends ConsumerStatefulWidget {
  const AiScreen({super.key});

  @override
  ConsumerState<AiScreen> createState() => _AiScreenState();
}

class _AiScreenState extends ConsumerState<AiScreen> {
  String _selectedSymbol = AppConstants.popularSymbols.first;
  AiSignalModel? _signal;
  bool _isLoading = false;
  String? _error;
  bool _isAutoTrading = false;
  double _autoStake = 1.0;

  Future<void> _analyse() async {
    setState(() { _isLoading = true; _error = null; });
    try {
      final signal = await ref.read(aiServiceProvider).getSignal(_selectedSymbol);
      setState(() { _signal = signal; _isLoading = false; });
    } catch (e) {
      setState(() { _error = e.toString(); _isLoading = false; });
    }
  }

  Future<void> _autoTrade() async {
    setState(() => _isAutoTrading = true);
    try {
      final result = await ref.read(aiServiceProvider).autoTrade(
        symbol: _selectedSymbol,
        stake: _autoStake,
        duration: 5,
        durationUnit: 't',
      );
      if (mounted) {
        final executed = result['executed'] as bool? ?? false;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(executed
              ? '✓ Trade executed: ${result['contract_type']} (${Fmt.confidence((result['confidence'] as num).toDouble())} confidence)'
              : '⏳ AI decided to WAIT — ${result['reason']}'),
          backgroundColor: executed ? AppColors.success : AppColors.warning,
        ));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Auto-trade error: $e'),
          backgroundColor: AppColors.danger,
        ));
      }
    } finally {
      if (mounted) setState(() => _isAutoTrading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AI Signal Engine')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ── Symbol picker ────────────────────────────────────────────────
          DropdownButtonFormField<String>(
            value: _selectedSymbol,
            decoration: const InputDecoration(
              labelText: 'Select Market',
              prefixIcon: Icon(Icons.auto_awesome),
            ),
            items: AppConstants.popularSymbols
                .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                .toList(),
            onChanged: (v) => setState(() => _selectedSymbol = v!),
          ),
          const SizedBox(height: 16),

          // ── Analyse button ────────────────────────────────────────────────
          ElevatedButton.icon(
            onPressed: _isLoading ? null : _analyse,
            icon: _isLoading
                ? const SizedBox(
                    width: 18, height: 18,
                    child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                  )
                : const Icon(Icons.search),
            label: Text(_isLoading ? 'Analysing...' : 'Analyse Market'),
          ),

          const SizedBox(height: 16),

          // ── Error ─────────────────────────────────────────────────────────
          if (_error != null)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.danger.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(_error!, style: const TextStyle(color: AppColors.danger)),
            ),

          // ── Signal card ───────────────────────────────────────────────────
          if (_signal != null) ...[
            _SignalCard(signal: _signal!),
            const SizedBox(height: 16),

            // ── Auto-trade section ──────────────────────────────────────────
            if (_signal!.signal != 'WAIT') ...[
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      initialValue: _autoStake.toString(),
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      decoration: const InputDecoration(
                        labelText: 'Stake (USD)',
                        prefixIcon: Icon(Icons.attach_money),
                      ),
                      onChanged: (v) => _autoStake = double.tryParse(v) ?? 1.0,
                    ),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton(
                    onPressed: _isAutoTrading ? null : _autoTrade,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _signal!.signal == 'BUY'
                          ? AppColors.success
                          : AppColors.danger,
                      minimumSize: const Size(120, 52),
                    ),
                    child: _isAutoTrading
                        ? const SizedBox(
                            width: 20, height: 20,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                        : Text(
                            '${_signal!.signal == 'BUY' ? '▲' : '▼'} Execute',
                            style: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                  ),
                ],
              ),
            ],
          ],
        ],
      ),
    );
  }
}

class _SignalCard extends StatelessWidget {
  final AiSignalModel signal;
  const _SignalCard({required this.signal});

  Color get _signalColor {
    switch (signal.signal) {
      case 'BUY':  return AppColors.buyColor;
      case 'SELL': return AppColors.sellColor;
      default:     return AppColors.waitColor;
    }
  }

  IconData get _signalIcon {
    switch (signal.signal) {
      case 'BUY':  return Icons.trending_up;
      case 'SELL': return Icons.trending_down;
      default:     return Icons.pause_circle_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _signalColor.withOpacity(0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _signalColor.withOpacity(0.3), width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Signal + confidence ───────────────────────────────────────────
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: _signalColor.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(_signalIcon, color: _signalColor, size: 28),
              ),
              const SizedBox(width: 16),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    signal.signal,
                    style: TextStyle(
                      color: _signalColor,
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  Text(
                    'Confidence: ${Fmt.confidence(signal.confidence)}',
                    style: const TextStyle(color: AppColors.textMuted),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),

          // ── Confidence bar ────────────────────────────────────────────────
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: signal.confidence,
              backgroundColor: _signalColor.withOpacity(0.15),
              valueColor: AlwaysStoppedAnimation(_signalColor),
              minHeight: 6,
            ),
          ),
          const SizedBox(height: 16),

          // ── Indicators row ────────────────────────────────────────────────
          Row(
            children: [
              _Chip(label: 'Trend', value: signal.trend, color: AppColors.info),
              const SizedBox(width: 8),
              _Chip(label: 'Vol', value: signal.volatility,
                color: signal.volatility == 'HIGH'
                    ? AppColors.danger
                    : signal.volatility == 'MEDIUM'
                        ? AppColors.warning
                        : AppColors.success),
              if (signal.pattern != null) ...[
                const SizedBox(width: 8),
                _Chip(label: 'Pattern', value: signal.pattern!,
                    color: AppColors.accent),
              ],
            ],
          ),
          const SizedBox(height: 12),

          // ── Reason ────────────────────────────────────────────────────────
          Text(
            'Reason',
            style: const TextStyle(
              color: AppColors.textMuted,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            signal.reason,
            style: const TextStyle(fontSize: 13),
          ),

          if (signal.entryPrice != null) ...[
            const SizedBox(height: 10),
            Row(
              children: [
                const Icon(Icons.place_outlined, size: 14, color: AppColors.textMuted),
                const SizedBox(width: 4),
                Text(
                  'Entry Price: ${signal.entryPrice!.toStringAsFixed(5)}',
                  style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                ),
              ],
            ),
          ],
        ],
      ),
    ).animate().fadeIn(duration: 400.ms).scale(begin: const Offset(0.95, 0.95));
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _Chip({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Text(label, style: TextStyle(color: color, fontSize: 9, fontWeight: FontWeight.w600)),
          Text(value, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}
