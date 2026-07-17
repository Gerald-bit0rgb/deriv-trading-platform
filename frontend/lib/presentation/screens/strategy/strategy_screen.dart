import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../../../data/models/strategy_settings_model.dart';
import '../../../data/services/strategy_service.dart';

// ── Providers ─────────────────────────────────────────────────────────────────

final strategyProvider =
    FutureProvider.autoDispose<StrategySettingsModel>((ref) {
  return ref.read(strategyServiceProvider).getSettings();
});

// ── Constants ──────────────────────────────────────────────────────────────────

// Candle timeframes — all Deriv-supported granularities
const _timeframes = [
  {'label': '1 Minute',   'value': 60},
  {'label': '2 Minutes',  'value': 120},
  {'label': '3 Minutes',  'value': 180},
  {'label': '5 Minutes',  'value': 300},
  {'label': '10 Minutes', 'value': 600},
  {'label': '15 Minutes', 'value': 900},
  {'label': '30 Minutes', 'value': 1800},
  {'label': '1 Hour',     'value': 3600},
  {'label': '2 Hours',    'value': 7200},
  {'label': '4 Hours',    'value': 14400},
  {'label': '8 Hours',    'value': 28800},
  {'label': '1 Day',      'value': 86400},
];

const _maMethods = ['EMA', 'SMA', 'WMA', 'SMMA'];

const _appliedPrices = [
  'CLOSE', 'OPEN', 'HIGH', 'LOW', 'MEDIAN', 'TYPICAL', 'WEIGHTED'
];

// ── Screen ─────────────────────────────────────────────────────────────────────

class StrategyScreen extends ConsumerStatefulWidget {
  const StrategyScreen({super.key});

  @override
  ConsumerState<StrategyScreen> createState() => _StrategyScreenState();
}

class _StrategyScreenState extends ConsumerState<StrategyScreen> {
  StrategySettingsModel? _settings;
  bool _isSaving = false;

  void _init(StrategySettingsModel s) {
    _settings ??= s;
  }

  Future<void> _save() async {
    if (_settings == null) return;
    setState(() => _isSaving = true);
    try {
      final updated =
          await ref.read(strategyServiceProvider).updateSettings(_settings!);
      setState(() {
        _settings = updated;
        _isSaving = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Strategy settings saved'),
          backgroundColor: AppColors.success,
        ));
      }
    } catch (e) {
      setState(() => _isSaving = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Error: $e'),
          backgroundColor: AppColors.danger,
        ));
      }
    }
  }

  Future<void> _reset() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Reset to Defaults'),
        content: const Text(
            'Reset all strategy settings to the original defaults?\n\n'
            'Trend: 4H EMA 5 / EMA 13\n'
            'Entry: 1M EMA 3 / BB(18) / MACD(12,26,9) / RSI(14)\n'
            'Exit: Crossback only (no duration)'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Reset'),
          ),
        ],
      ),
    );
    if (confirm != true) return;
    setState(() => _isSaving = true);
    try {
      final defaults =
          await ref.read(strategyServiceProvider).resetSettings();
      setState(() {
        _settings = defaults;
        _isSaving = false;
      });
      ref.invalidate(strategyProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Settings reset to defaults'),
          backgroundColor: AppColors.info,
        ));
      }
    } catch (e) {
      setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(strategyProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Strategy Settings'),
        actions: [
          IconButton(
            icon: const Icon(Icons.restore),
            tooltip: 'Reset to defaults',
            onPressed: _isSaving ? null : _reset,
          ),
          IconButton(
            icon: _isSaving
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: AppColors.primary),
                  )
                : const Icon(Icons.save_outlined),
            onPressed: _isSaving ? null : _save,
          ),
        ],
      ),
      body: async.when(
        loading: () =>
            const Center(child: CircularProgressIndicator(color: AppColors.primary)),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (s) {
          _init(s);
          if (_settings == null) return const SizedBox();
          return _buildForm();
        },
      ),
    );
  }

  Widget _buildForm() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // ── Info banner ────────────────────────────────────────────────────
        Container(
          padding: const EdgeInsets.all(12),
          margin: const EdgeInsets.only(bottom: 16),
          decoration: BoxDecoration(
            color: AppColors.info.withOpacity(0.1),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: AppColors.info.withOpacity(0.3)),
          ),
          child: const Row(
            children: [
              Icon(Icons.info_outline, color: AppColors.info, size: 16),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Changes apply on the next bot restart. Tap ↺ to reset to defaults.',
                  style: TextStyle(fontSize: 12, color: AppColors.info),
                ),
              ),
            ],
          ),
        ),

        // ── TREND DIRECTION SECTION ─────────────────────────────────────────
        _SectionHeader(
          title: 'TREND DIRECTION',
          subtitle: 'Higher-timeframe filter — gates every entry (e.g. 4H EMA 5 vs EMA 13)',
          color: AppColors.primary,
        ),
        SwitchListTile(
          title: const Text('Require Trend Alignment',
              style: TextStyle(fontWeight: FontWeight.w600)),
          subtitle: const Text(
            'BUY only when trend is bullish, SELL only when bearish.\n'
            'Turn off to trade the 1M confirmation signals alone.',
            style: TextStyle(fontSize: 12, color: AppColors.textMuted),
          ),
          value: _settings!.requireTrendAlignment,
          onChanged: (v) => setState(
              () => _settings = _settings!.copyWith(requireTrendAlignment: v)),
          activeColor: AppColors.primary,
          contentPadding: EdgeInsets.zero,
        ),
        const SizedBox(height: 8),
        _TfDropdown(
          label: 'Trend Timeframe',
          value: _settings!.trendTimeframe,
          onChanged: (v) =>
              setState(() => _settings = _settings!.copyWith(trendTimeframe: v)),
        ),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(
            child: _IntField(
              label: 'Fast MA Period',
              value: _settings!.trendFastPeriod,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(trendFastPeriod: v)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _IntField(
              label: 'Slow MA Period',
              value: _settings!.trendSlowPeriod,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(trendSlowPeriod: v)),
            ),
          ),
        ]),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(
            child: _DropField(
              label: 'MA Method',
              value: _settings!.trendMaMethod,
              items: _maMethods,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(trendMaMethod: v)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _DropField(
              label: 'Applied Price',
              value: _settings!.trendAppliedPrice,
              items: _appliedPrices,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(trendAppliedPrice: v)),
            ),
          ),
        ]),

        const SizedBox(height: 24),

        // ── ENTRY CONFIRMATION SECTION ───────────────────────────────────────
        _SectionHeader(
          title: 'ENTRY CONFIRMATION',
          subtitle: 'Microtrading signal — EMA / Bollinger Bands / MACD / RSI',
          color: AppColors.accent,
        ),
        _TfDropdown(
          label: 'Entry Timeframe',
          value: _settings!.entryTimeframe,
          onChanged: (v) =>
              setState(() => _settings = _settings!.copyWith(entryTimeframe: v)),
        ),
        const SizedBox(height: 16),

        _SubHeader(title: 'EMA (fast entry line)'),
        Row(children: [
          Expanded(
            child: _IntField(
              label: 'EMA Period',
              value: _settings!.emaFastPeriod,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(emaFastPeriod: v)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _DropField(
              label: 'Applied Price',
              value: _settings!.emaAppliedPrice,
              items: _appliedPrices,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(emaAppliedPrice: v)),
            ),
          ),
        ]),
        const SizedBox(height: 16),

        _SubHeader(title: 'Bollinger Bands (signal line)'),
        Row(children: [
          Expanded(
            child: _IntField(
              label: 'BB Period',
              value: _settings!.bbPeriod,
              onChanged: (v) =>
                  setState(() => _settings = _settings!.copyWith(bbPeriod: v)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _DoubleField(
              label: 'Std Dev',
              hint: 'e.g. 2.0',
              value: _settings!.bbStdDev,
              onChanged: (v) =>
                  setState(() => _settings = _settings!.copyWith(bbStdDev: v)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _DropField(
              label: 'Method',
              value: _settings!.bbMethod,
              items: const ['SMA', 'EMA'],
              onChanged: (v) =>
                  setState(() => _settings = _settings!.copyWith(bbMethod: v)),
            ),
          ),
        ]),
        const SizedBox(height: 16),

        _SubHeader(title: 'MACD Histogram'),
        Row(children: [
          Expanded(
            child: _IntField(
              label: 'Fast',
              value: _settings!.macdFast,
              onChanged: (v) =>
                  setState(() => _settings = _settings!.copyWith(macdFast: v)),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: _IntField(
              label: 'Slow',
              value: _settings!.macdSlow,
              onChanged: (v) =>
                  setState(() => _settings = _settings!.copyWith(macdSlow: v)),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: _IntField(
              label: 'Signal',
              value: _settings!.macdSignal,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(macdSignal: v)),
            ),
          ),
        ]),
        const SizedBox(height: 16),

        _SubHeader(title: 'RSI'),
        Row(children: [
          Expanded(
            child: _IntField(
              label: 'RSI Period',
              value: _settings!.rsiPeriod,
              onChanged: (v) =>
                  setState(() => _settings = _settings!.copyWith(rsiPeriod: v)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _DoubleField(
              label: 'Overbought',
              hint: 'e.g. 70',
              value: _settings!.rsiOverbought,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(rsiOverbought: v)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _DoubleField(
              label: 'Oversold',
              hint: 'e.g. 30',
              value: _settings!.rsiOversold,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(rsiOversold: v)),
            ),
          ),
        ]),
        Container(
          padding: const EdgeInsets.all(10),
          margin: const EdgeInsets.only(top: 8),
          decoration: BoxDecoration(
            color: AppColors.info.withOpacity(0.08),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: AppColors.info.withOpacity(0.3)),
          ),
          child: const Text(
            'Entry uses a fixed RSI > 50 / < 50 midline check, not these '
            'overbought/oversold levels — they\'re kept here for your own '
            'reference and future strategy tuning.',
            style: TextStyle(fontSize: 12, color: AppColors.info),
          ),
        ),

        const SizedBox(height: 24),

        // ── EXIT SECTION ──────────────────────────────────────────────────
        _SectionHeader(
          title: 'EXIT — CROSSBACK',
          subtitle: 'EA-style exit — no fixed duration',
          color: AppColors.primary,
        ),
        SwitchListTile(
          title: const Text('Enable Crossback Exit',
              style: TextStyle(fontWeight: FontWeight.w600)),
          subtitle: const Text(
            'BUY closes when EMA crosses BELOW BB middle.\n'
            'SELL closes when EMA crosses ABOVE BB middle.\n'
            'Combine with Trailing Stop (Risk Settings) to lock in profit sooner.',
            style: TextStyle(fontSize: 12, color: AppColors.textMuted),
          ),
          value: _settings!.exitOnCrossbackEnabled,
          onChanged: (v) => setState(() =>
              _settings = _settings!.copyWith(exitOnCrossbackEnabled: v)),
          activeColor: AppColors.primary,
          contentPadding: EdgeInsets.zero,
        ),

        const SizedBox(height: 24),

        // ── ATR STOP LOSS / TAKE PROFIT SECTION ──────────────────────────────
        _SectionHeader(
          title: 'ATR STOP LOSS / TAKE PROFIT',
          subtitle: 'Optional — sets price-based exits from entry, sized to current volatility',
          color: AppColors.accent,
        ),
        SwitchListTile(
          title: const Text('Enable ATR Stop Loss / Take Profit',
              style: TextStyle(fontWeight: FontWeight.w600)),
          subtitle: const Text(
            'At entry, SL/TP are set at entry price ± (ATR × multiplier).\n'
            'Works alongside crossback and trailing stop — whichever '
            'condition is met first closes the trade.',
            style: TextStyle(fontSize: 12, color: AppColors.textMuted),
          ),
          value: _settings!.useAtrSlTp,
          onChanged: (v) => setState(
              () => _settings = _settings!.copyWith(useAtrSlTp: v)),
          activeColor: AppColors.accent,
          contentPadding: EdgeInsets.zero,
        ),
        if (_settings!.useAtrSlTp) ...[
          const SizedBox(height: 8),
          _IntField(
            label: 'ATR Period',
            value: _settings!.atrPeriod,
            onChanged: (v) =>
                setState(() => _settings = _settings!.copyWith(atrPeriod: v)),
          ),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(
              child: _DoubleField(
                label: 'Stop Loss Multiplier',
                hint: 'e.g. 1.5',
                value: _settings!.atrSlMultiplier,
                onChanged: (v) => setState(() =>
                    _settings = _settings!.copyWith(atrSlMultiplier: v)),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _DoubleField(
                label: 'Take Profit Multiplier',
                hint: 'e.g. 2.0',
                value: _settings!.atrTpMultiplier,
                onChanged: (v) => setState(() =>
                    _settings = _settings!.copyWith(atrTpMultiplier: v)),
              ),
            ),
          ]),
        ],

        const SizedBox(height: 32),

        // ── Save button ────────────────────────────────────────────────────
        ElevatedButton.icon(
          onPressed: _isSaving ? null : _save,
          icon: _isSaving
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                      color: Colors.white, strokeWidth: 2))
              : const Icon(Icons.save),
          label: const Text('Save Strategy Settings'),
        ),
        const SizedBox(height: 24),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Helper widgets
// ─────────────────────────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  final String title;
  final String subtitle;
  final Color color;
  const _SectionHeader(
      {required this.title, required this.subtitle, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(8),
        border: Border(left: BorderSide(color: color, width: 3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.w800,
                  fontSize: 13,
                  letterSpacing: 0.5)),
          Text(subtitle,
              style:
                  const TextStyle(color: AppColors.textMuted, fontSize: 11)),
        ],
      ),
    );
  }
}

class _SubHeader extends StatelessWidget {
  final String title;
  const _SubHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(title,
          style: const TextStyle(
              color: AppColors.textMuted,
              fontSize: 11,
              fontWeight: FontWeight.w600)),
    );
  }
}

class _TfDropdown extends StatelessWidget {
  final String label;
  final int value;
  final ValueChanged<int> onChanged;
  const _TfDropdown(
      {required this.label, required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<int>(
      value: value,
      decoration: InputDecoration(labelText: label),
      items: _timeframes
          .map((tf) => DropdownMenuItem<int>(
                value: tf['value'] as int,
                child: Text(tf['label'] as String),
              ))
          .toList(),
      onChanged: (v) => onChanged(v!),
    );
  }
}

class _DropField extends StatelessWidget {
  final String label;
  final String value;
  final List<String> items;
  final ValueChanged<String> onChanged;
  const _DropField(
      {required this.label,
      required this.value,
      required this.items,
      required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<String>(
      value: value,
      decoration: InputDecoration(labelText: label),
      items: items
          .map((i) => DropdownMenuItem(value: i, child: Text(i)))
          .toList(),
      onChanged: (v) => onChanged(v!),
    );
  }
}

class _IntField extends StatelessWidget {
  final String label;
  final int value;
  final ValueChanged<int> onChanged;
  const _IntField(
      {required this.label, required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      initialValue: value.toString(),
      keyboardType: TextInputType.number,
      decoration: InputDecoration(labelText: label),
      onChanged: (v) {
        final n = int.tryParse(v);
        if (n != null && n > 0) onChanged(n);
      },
    );
  }
}

class _DoubleField extends StatelessWidget {
  final String label;
  final double value;
  final String hint;
  final ValueChanged<double> onChanged;
  const _DoubleField(
      {required this.label,
      required this.value,
      required this.hint,
      required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      initialValue: value.toString(),
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(labelText: label, hintText: hint),
      onChanged: (v) {
        final n = double.tryParse(v);
        if (n != null && n >= 0) onChanged(n);
      },
    );
  }
}
