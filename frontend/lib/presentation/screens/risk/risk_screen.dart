import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../../../data/models/risk_settings_model.dart';
import '../../../data/services/risk_service.dart';

final riskSettingsProvider = FutureProvider.autoDispose<RiskSettingsModel>((ref) {
  return ref.read(riskServiceProvider).getRiskSettings();
});

class RiskScreen extends ConsumerStatefulWidget {
  const RiskScreen({super.key});

  @override
  ConsumerState<RiskScreen> createState() => _RiskScreenState();
}

class _RiskScreenState extends ConsumerState<RiskScreen> {
  RiskSettingsModel? _settings;
  bool _isSaving = false;

  void _initSettings(RiskSettingsModel s) {
    _settings ??= s;
  }

  Future<void> _save() async {
    if (_settings == null) return;
    setState(() => _isSaving = true);
    try {
      final updated = await ref.read(riskServiceProvider).updateRiskSettings(_settings!);
      setState(() { _settings = updated; _isSaving = false; });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Risk settings saved'),
              backgroundColor: AppColors.success),
        );
      }
    } catch (e) {
      setState(() => _isSaving = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: AppColors.danger),
        );
      }
    }
  }

  Future<void> _emergencyStop() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Emergency Stop'),
        content: const Text(
            'This will immediately stop ALL trading and disable the bot. Continue?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger),
            child: const Text('STOP EVERYTHING'),
          ),
        ],
      ),
    );
    if (confirm == true) {
      await ref.read(riskServiceProvider).emergencyStop();
      ref.invalidate(riskSettingsProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Emergency stop activated'),
              backgroundColor: AppColors.danger),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final riskAsync = ref.watch(riskSettingsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Risk Management'),
        actions: [
          if (_settings != null)
            IconButton(
              icon: _isSaving
                  ? const SizedBox(width: 20, height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.save_outlined),
              onPressed: _isSaving ? null : _save,
            ),
        ],
      ),
      body: riskAsync.when(
        loading: () => const Center(child: CircularProgressIndicator(color: AppColors.primary)),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (settings) {
          _initSettings(settings);
          if (_settings == null) return const SizedBox();
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // ── Emergency stop button ───────────────────────────────────────
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.danger.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppColors.danger.withOpacity(0.3)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.warning_amber_rounded, color: AppColors.danger),
                        SizedBox(width: 8),
                        Text('Emergency Controls',
                            style: TextStyle(
                                color: AppColors.danger, fontWeight: FontWeight.w700)),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: _emergencyStop,
                            icon: const Icon(Icons.stop_circle),
                            label: const Text('EMERGENCY STOP'),
                            style: ElevatedButton.styleFrom(
                                backgroundColor: AppColors.danger),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: () async {
                              await ref.read(riskServiceProvider).emergencyReset();
                              ref.invalidate(riskSettingsProvider);
                            },
                            icon: const Icon(Icons.play_circle_outline),
                            label: const Text('Reset'),
                            style: OutlinedButton.styleFrom(
                                foregroundColor: AppColors.success),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // ── Toggle: trading enabled ──────────────────────────────────────
              _SwitchTile(
                title: 'Trading Enabled',
                subtitle: 'Enable or disable all automated trading',
                value: _settings!.tradingEnabled,
                onChanged: (v) => setState(() =>
                    _settings = _settings!.copyWith(tradingEnabled: v)),
              ),

              const _SectionTitle('Position Sizing'),
              _SliderTile(
                label: 'Default Stake',
                value: _settings!.defaultStake,
                min: 0.35, max: 100, divisions: 200,
                format: (v) => '\$${v.toStringAsFixed(2)}',
                onChanged: (v) => setState(() =>
                    _settings = _settings!.copyWith(defaultStake: v)),
              ),
              _SliderTile(
                label: 'Max Stake',
                value: _settings!.maxStake,
                min: 1, max: 1000, divisions: 999,
                format: (v) => '\$${v.toStringAsFixed(0)}',
                onChanged: (v) => setState(() =>
                    _settings = _settings!.copyWith(maxStake: v)),
              ),

              const _SectionTitle('Daily Limits'),
              _SliderTile(
                label: 'Max Daily Loss',
                value: _settings!.maxDailyLoss,
                min: 1, max: 500, divisions: 499,
                format: (v) => '\$${v.toStringAsFixed(0)}',
                onChanged: (v) => setState(() =>
                    _settings = _settings!.copyWith(maxDailyLoss: v)),
              ),
              _SliderTile(
                label: 'Daily Profit Target',
                value: _settings!.dailyProfitTarget,
                min: 1, max: 1000, divisions: 999,
                format: (v) => '\$${v.toStringAsFixed(0)}',
                onChanged: (v) => setState(() =>
                    _settings = _settings!.copyWith(dailyProfitTarget: v)),
              ),

              const _SectionTitle('Concurrent Positions'),
              _SliderTile(
                label: 'Max Open Trades',
                value: _settings!.maxOpenTrades.toDouble(),
                min: 1, max: 20, divisions: 19,
                format: (v) => '${v.toInt()} trades',
                onChanged: (v) => setState(() =>
                    _settings = _settings!.copyWith(maxOpenTrades: v.toInt())),
              ),

              const _SectionTitle('Drawdown Protection'),
              _SliderTile(
                label: 'Max Drawdown',
                value: _settings!.maxDrawdownPct,
                min: 1, max: 100, divisions: 99,
                format: (v) => '${v.toStringAsFixed(0)}%',
                onChanged: (v) => setState(() =>
                    _settings = _settings!.copyWith(maxDrawdownPct: v)),
              ),

              const _SectionTitle('AI Settings'),
              _SliderTile(
                label: 'Min AI Confidence',
                value: _settings!.minAiConfidence * 100,
                min: 30, max: 95, divisions: 65,
                format: (v) => '${v.toStringAsFixed(0)}%',
                onChanged: (v) => setState(() =>
                    _settings = _settings!.copyWith(minAiConfidence: v / 100)),
              ),

              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _isSaving ? null : _save,
                child: _isSaving
                    ? const SizedBox(height: 20, width: 20,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Text('Save Risk Settings'),
              ),
              const SizedBox(height: 24),
            ],
          );
        },
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String title;
  const _SectionTitle(this.title);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(0, 20, 0, 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleSmall?.copyWith(
          color: AppColors.primary,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}

class _SliderTile extends StatelessWidget {
  final String label;
  final double value;
  final double min;
  final double max;
  final int? divisions;
  final String Function(double) format;
  final ValueChanged<double> onChanged;

  const _SliderTile({
    required this.label,
    required this.value,
    required this.min,
    required this.max,
    this.divisions,
    required this.format,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(fontSize: 14)),
            Text(format(value),
                style: const TextStyle(
                    color: AppColors.primary, fontWeight: FontWeight.w700)),
          ],
        ),
        Slider(
          value: value.clamp(min, max),
          min: min, max: max,
          divisions: divisions,
          activeColor: AppColors.primary,
          onChanged: onChanged,
        ),
      ],
    );
  }
}

class _SwitchTile extends StatelessWidget {
  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;

  const _SwitchTile({
    required this.title,
    required this.subtitle,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return SwitchListTile(
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
      subtitle: Text(subtitle,
          style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
      value: value,
      onChanged: onChanged,
      activeColor: AppColors.primary,
    );
  }
}
