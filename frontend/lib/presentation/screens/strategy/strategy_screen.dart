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

const _timeframes = [
  {'label': '1 Minute',  'value': 60},
  {'label': '5 Minutes', 'value': 300},
  {'label': '10 Minutes','value': 600},
  {'label': '15 Minutes','value': 900},
  {'label': '30 Minutes','value': 1800},
  {'label': '1 Hour',    'value': 3600},
  {'label': '2 Hours',   'value': 7200},
  {'label': '4 Hours',   'value': 14400},
  {'label': '8 Hours',   'value': 28800},
  {'label': '1 Day',     'value': 86400},
];

const _maMethods = ['EMA', 'SMA', 'WMA', 'SMMA'];

const _appliedPrices = [
  'CLOSE', 'OPEN', 'HIGH', 'LOW', 'MEDIAN', 'TYPICAL', 'WEIGHTED'
];

const _durationUnits = [
  {'label': 'Ticks',   'value': 't'},
  {'label': 'Seconds', 'value': 's'},
  {'label': 'Minutes', 'value': 'm'},
  {'label': 'Hours',   'value': 'h'},
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
            'Reset all strategy settings to the original EA defaults?\n\n'
            '4H EMA5/EMA13 bias + ADX(14) >= 20\n'
            '15M EMA5 vs SMA50 on Typical Price\n'
            'Emergency exit on SMA50\n'
            '5 ticks duration'),
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
          content: Text('Settings reset to EA defaults'),
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
          // Reset button
          IconButton(
            icon: const Icon(Icons.restore),
            tooltip: 'Reset to EA defaults',
            onPressed: _isSaving ? null : _reset,
          ),
          // Save button
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
                  'Changes apply on the next bot restart. Tap ↺ to reset to EA defaults.',
                  style: TextStyle(fontSize: 12, color: AppColors.info),
                ),
              ),
            ],
          ),
        ),

        // ── BIAS TIMEFRAME SECTION ─────────────────────────────────────────
        _SectionHeader(
          title: 'BIAS TIMEFRAME',
          subtitle: 'Determines market direction (like your 4H)',
          color: AppColors.primary,
        ),
        _TfDropdown(
          label: 'Bias Timeframe',
          value: _settings!.biasTimeframe,
          onChanged: (v) =>
              setState(() => _settings = _settings!.copyWith(biasTimeframe: v)),
        ),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(
            child: _IntField(
              label: 'Fast Period',
              value: _settings!.biasFastPeriod,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(biasFastPeriod: v)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _IntField(
              label: 'Slow Period',
              value: _settings!.biasSlowPeriod,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(biasSlowPeriod: v)),
            ),
          ),
        ]),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(
            child: _DropField(
              label: 'MA Method',
              value: _settings!.biasMaMethod,
              items: _maMethods,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(biasMaMethod: v)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _DropField(
              label: 'Applied Price',
              value: _settings!.biasAppliedPrice,
              items: _appliedPrices,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(biasAppliedPrice: v)),
            ),
          ),
        ]),

        const SizedBox(height: 24),

        // ── ADX FILTER SECTION ─────────────────────────────────────────────
        _SectionHeader(
          title: 'ADX FILTER',
          subtitle: 'Confirms trend strength before entry',
          color: AppColors.warning,
        ),
        SwitchListTile(
          title: const Text('Enable ADX Filter',
              style: TextStyle(fontWeight: FontWeight.w600)),
          subtitle: const Text('Only trade when trend is strong enough',
              style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
          value: _settings!.adxEnabled,
          onChanged: (v) =>
              setState(() => _settings = _settings!.copyWith(adxEnabled: v)),
          activeColor: AppColors.warning,
          contentPadding: EdgeInsets.zero,
        ),
        if (_settings!.adxEnabled) ...[
          Row(children: [
            Expanded(
              child: _IntField(
                label: 'ADX Period',
                value: _settings!.adxPeriod,
                onChanged: (v) => setState(
                    () => _settings = _settings!.copyWith(adxPeriod: v)),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _DoubleField(
                label: 'ADX Threshold',
                value: _settings!.adxThreshold,
                hint: 'e.g. 20.0',
                onChanged: (v) => setState(
                    () => _settings = _settings!.copyWith(adxThreshold: v)),
              ),
            ),
          ]),
        ],

        const SizedBox(height: 24),

        // ── ENTRY TIMEFRAME SECTION ────────────────────────────────────────
        _SectionHeader(
          title: 'ENTRY TIMEFRAME',
          subtitle: 'Triggers the actual trade (like your 15M)',
          color: AppColors.success,
        ),
        _TfDropdown(
          label: 'Entry Timeframe',
          value: _settings!.entryTimeframe,
          onChanged: (v) =>
              setState(() => _settings = _settings!.copyWith(entryTimeframe: v)),
        ),
        const SizedBox(height: 12),

        // Fast MA
        const _SubHeader(title: 'Fast MA (EMA5 in EA)'),
        Row(children: [
          Expanded(
            child: _IntField(
              label: 'Fast Period',
              value: _settings!.entryFastPeriod,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(entryFastPeriod: v)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _DropField(
              label: 'Fast Method',
              value: _settings!.entryFastMethod,
              items: _maMethods,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(entryFastMethod: v)),
            ),
          ),
        ]),
        const SizedBox(height: 12),

        // Slow MA
        const _SubHeader(title: 'Slow MA (SMA50 in EA)'),
        Row(children: [
          Expanded(
            child: _IntField(
              label: 'Slow Period',
              value: _settings!.entrySlowPeriod,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(entrySlowPeriod: v)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _DropField(
              label: 'Slow Method',
              value: _settings!.entrySlowMethod,
              items: _maMethods,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(entrySlowMethod: v)),
            ),
          ),
        ]),
        const SizedBox(height: 12),

        _DropField(
          label: 'Applied Price (both entry MAs)',
          value: _settings!.entryAppliedPrice,
          items: _appliedPrices,
          onChanged: (v) => setState(
              () => _settings = _settings!.copyWith(entryAppliedPrice: v)),
        ),

        const SizedBox(height: 24),

        // ── EMERGENCY EXIT SECTION ─────────────────────────────────────────
        _SectionHeader(
          title: 'EMERGENCY EXIT',
          subtitle: 'Closes basket when candle crosses SMA',
          color: AppColors.danger,
        ),
        SwitchListTile(
          title: const Text('Enable Emergency Exit',
              style: TextStyle(fontWeight: FontWeight.w600)),
          subtitle: const Text(
              'Close all trades if candle closes against the SMA',
              style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
          value: _settings!.emergencyExitEnabled,
          onChanged: (v) => setState(
              () => _settings = _settings!.copyWith(emergencyExitEnabled: v)),
          activeColor: AppColors.danger,
          contentPadding: EdgeInsets.zero,
        ),
        if (_settings!.emergencyExitEnabled)
          _IntField(
            label: 'Exit SMA Period (default: 50)',
            value: _settings!.exitSmaPeriod,
            onChanged: (v) => setState(
                () => _settings = _settings!.copyWith(exitSmaPeriod: v)),
          ),

        const SizedBox(height: 24),

        // ── CANDLE CONFIRMATION SECTION ────────────────────────────────────
        _SectionHeader(
          title: 'CANDLE CONFIRMATION',
          subtitle:
              'Require 2 consecutive candles to confirm entry signal',
          color: AppColors.accent,
        ),
        SwitchListTile(
          title: const Text('Require 2-Candle Confirmation',
              style: TextStyle(fontWeight: FontWeight.w600)),
          subtitle: const Text(
            'Both current AND previous candle must close on the same\n'
            'side of the fast MA before entering a trade.\n'
            'OFF = original EA logic (1 candle only)\n'
            'ON = stricter filter, fewer but higher quality signals',
            style: TextStyle(fontSize: 12, color: AppColors.textMuted),
          ),
          value: _settings!.requireCandleConfirmation,
          onChanged: (v) => setState(() => _settings =
              _settings!.copyWith(requireCandleConfirmation: v)),
          activeColor: AppColors.accent,
          contentPadding: EdgeInsets.zero,
        ),

        const SizedBox(height: 24),

        // ── TRADE DURATION SECTION ─────────────────────────────────────────
        _SectionHeader(
          title: 'TRADE DURATION',
          subtitle: 'How long each contract runs',
          color: AppColors.accent,
        ),
        Row(children: [
          Expanded(
            child: _IntField(
              label: 'Duration',
              value: _settings!.tradeDuration,
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(tradeDuration: v)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: DropdownButtonFormField<String>(
              value: _settings!.tradeDurationUnit,
              decoration: const InputDecoration(labelText: 'Unit'),
              items: _durationUnits
                  .map((u) => DropdownMenuItem(
                        value: u['value'] as String,
                        child: Text(u['label'] as String),
                      ))
                  .toList(),
              onChanged: (v) => setState(
                  () => _settings = _settings!.copyWith(tradeDurationUnit: v)),
            ),
          ),
        ]),

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
