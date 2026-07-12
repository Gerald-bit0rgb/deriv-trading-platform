import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/providers/account_type_provider.dart';
import '../../../data/providers/auth_provider.dart';
import '../../../data/providers/bot_symbol_provider.dart';
import '../../../data/providers/dashboard_provider.dart';
import '../../widgets/charts/equity_chart.dart';
import '../../widgets/common/stat_card.dart';

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(AppConstants.dashboardRefreshInterval, (_) {
      ref.invalidate(dashboardProvider);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dashAsync = ref.watch(dashboardProvider);
    final botStatus = ref.watch(botStatusProvider);
    final user = ref.watch(authProvider).user;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          children: [
            const Text('Dashboard'),
            Text(
              'Welcome, ${user?.username ?? ''}',
              style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () => context.go('/notifications'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(dashboardProvider),
        child: dashAsync.when(
          loading: () => const _DashboardSkeleton(),
          error: (e, _) => _ErrorView(
            error: e.toString().contains('500')
                ? 'Server is starting up. Pull down to refresh.'
                : e.toString().contains('401')
                    ? 'Session expired. Please log in again.'
                    : 'Could not load dashboard. Pull down to retry.',
            onRetry: () => ref.invalidate(dashboardProvider),
          ),
          data: (data) => _DashboardContent(data: data, botStatus: botStatus),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Main content
// ─────────────────────────────────────────────────────────────────────────────

class _DashboardContent extends ConsumerWidget {
  final Map<String, dynamic> data;
  final String botStatus;

  const _DashboardContent({required this.data, required this.botStatus});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final account  = data['account']  as Map<String, dynamic>? ?? {};
    final today    = data['today']    as Map<String, dynamic>? ?? {};
    final allTime  = data['all_time'] as Map<String, dynamic>? ?? {};
    final riskData = data['risk']     as Map<String, dynamic>? ?? {};
    final curve    = data['equity_curve'] as List<dynamic>? ?? [];

    final balance  = account['balance'] as num?;
    final currency = account['currency'] as String? ?? 'USD';
    final todayP   = (today['profit'] as num?)?.toDouble() ?? 0;
    final winRate  = (today['win_rate'] as num?)?.toDouble() ?? 0;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // ── Balance card ──────────────────────────────────────────────────────
        _BalanceCard(
          balance: balance?.toDouble(),
          currency: currency,
          botStatus: botStatus,
        ).animate().fadeIn(duration: 300.ms),

        const SizedBox(height: 12),

        // ── Account type switcher (Demo / Real) ───────────────────────────────
        const _AccountTypeSwitcher(),

        const SizedBox(height: 12),

        // ── Symbol selector ───────────────────────────────────────────────────
        const _BotSymbolSelector(),

        const SizedBox(height: 12),

        // ── Bot control strip ─────────────────────────────────────────────────
        _BotControlStrip(botStatus: botStatus),

        const SizedBox(height: 16),

        // ── Today stats ───────────────────────────────────────────────────────
        Text('Today',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          mainAxisSpacing: 10,
          crossAxisSpacing: 10,
          childAspectRatio: 1.5,
          children: [
            StatCard(
              label: 'P/L Today',
              value: Fmt.signedMoney(todayP),
              icon: Icons.trending_up,
              valueColor: todayP >= 0 ? AppColors.success : AppColors.danger,
              iconColor: todayP >= 0 ? AppColors.success : AppColors.danger,
            ),
            StatCard(
              label: 'Win Rate',
              value: Fmt.pct(winRate),
              icon: Icons.emoji_events_outlined,
              iconColor: AppColors.warning,
            ),
            StatCard(
              label: "Today's Trades",
              value: '${today['trades'] ?? 0}',
              icon: Icons.swap_horiz,
              iconColor: AppColors.info,
            ),
            StatCard(
              label: 'Open Trades',
              value: '${data['open_trades'] ?? 0}',
              icon: Icons.access_time,
              iconColor: AppColors.primary,
              onTap: () => context.go('/trading'),
            ),
          ],
        ).animate().fadeIn(delay: 100.ms),

        const SizedBox(height: 16),

        // ── All-time stats ────────────────────────────────────────────────────
        Text('All-Time',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          mainAxisSpacing: 10,
          crossAxisSpacing: 10,
          childAspectRatio: 1.5,
          children: [
            StatCard(
              label: 'Total Profit',
              value: Fmt.money((allTime['total_profit'] as num?)?.toDouble()),
              icon: Icons.account_balance_wallet_outlined,
              iconColor: AppColors.success,
            ),
            StatCard(
              label: 'Total Trades',
              value: '${allTime['total_trades'] ?? 0}',
              icon: Icons.bar_chart,
              iconColor: AppColors.accent,
            ),
          ],
        ).animate().fadeIn(delay: 150.ms),

        const SizedBox(height: 16),

        // ── Equity chart ──────────────────────────────────────────────────────
        Text('7-Day Equity Curve',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        EquityChart(equityCurve: curve).animate().fadeIn(delay: 200.ms),

        const SizedBox(height: 16),

        // ── Risk status ───────────────────────────────────────────────────────
        _RiskStatusCard(riskData: riskData),

        const SizedBox(height: 24),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Account Type Switcher (Demo / Real)
// ─────────────────────────────────────────────────────────────────────────────

class _AccountTypeSwitcher extends ConsumerWidget {
  const _AccountTypeSwitcher();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final accountType = ref.watch(accountTypeProvider);
    final isDemo = accountType == 'demo';

    return Container(
      padding: const EdgeInsets.all(12),
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
          Row(
            children: [
              Icon(
                Icons.account_balance,
                size: 16,
                color: isDemo ? AppColors.warning : AppColors.success,
              ),
              const SizedBox(width: 6),
              Text(
                'Account Type',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: AppColors.textMuted,
                ),
              ),
              const Spacer(),
              // Demo badge
              _TypeBadge(
                label: 'DEMO',
                selected: isDemo,
                color: AppColors.warning,
                onTap: () =>
                    ref.read(accountTypeProvider.notifier).setType('demo'),
              ),
              const SizedBox(width: 8),
              // Real badge
              _TypeBadge(
                label: 'REAL',
                selected: !isDemo,
                color: AppColors.success,
                onTap: () => _confirmReal(context, ref),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            isDemo
                ? 'Trading with virtual money. Safe to practise.'
                : '⚠️  REAL MONEY — trades use your actual funds.',
            style: TextStyle(
              fontSize: 11,
              color: isDemo ? AppColors.textMuted : AppColors.danger,
              fontWeight: isDemo ? FontWeight.normal : FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  void _confirmReal(BuildContext context, WidgetRef ref) {
    showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Switch to Real Account'),
        content: const Text(
          'You are about to switch to REAL MONEY trading.\n\n'
          'All trades will use your actual Deriv balance.\n\n'
          'Make sure you have tested on a demo account first.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Stay on Demo'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style:
                ElevatedButton.styleFrom(backgroundColor: AppColors.danger),
            child: const Text('Switch to Real'),
          ),
        ],
      ),
    ).then((confirmed) {
      if (confirmed == true) {
        ref.read(accountTypeProvider.notifier).setType('real');
      }
    });
  }
}

class _TypeBadge extends StatelessWidget {
  final String label;
  final bool selected;
  final Color color;
  final VoidCallback onTap;

  const _TypeBadge({
    required this.label,
    required this.selected,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
        decoration: BoxDecoration(
          color: selected ? color : color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: color),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: selected ? Colors.white : color,
            fontWeight: FontWeight.w700,
            fontSize: 12,
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Bot Symbol Selector
// ─────────────────────────────────────────────────────────────────────────────

class _BotSymbolSelector extends ConsumerWidget {
  const _BotSymbolSelector();

  // Group name helper
  static String _groupName(String symbol) {
    if (symbol.startsWith('1HZ')) return 'Volatility (1s)';
    if (symbol.startsWith('JD'))  return 'Jump Index';
    if (symbol.startsWith('R_'))  return 'Volatility';
    return 'Forex';
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selected = ref.watch(botSymbolProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    // Find display name
    final allSymbols = AppConstants.allSymbols;
    final selectedMap = allSymbols.firstWhere(
      (s) => s['symbol'] == selected,
      orElse: () => {'symbol': selected, 'name': selected},
    );

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : AppColors.lightCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
        ),
      ),
      child: Row(
        children: [
          const Icon(Icons.candlestick_chart,
              size: 18, color: AppColors.primary),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Bot Trading Pair',
                    style: TextStyle(
                        fontSize: 11,
                        color: AppColors.textMuted,
                        fontWeight: FontWeight.w500)),
                const SizedBox(height: 2),
                Text(
                  selectedMap['name']!,
                  style: const TextStyle(
                      fontWeight: FontWeight.w700, fontSize: 14),
                ),
              ],
            ),
          ),
          TextButton(
            onPressed: () => _showSymbolPicker(context, ref, selected),
            child: const Text('Change'),
          ),
        ],
      ),
    );
  }

  void _showSymbolPicker(BuildContext context, WidgetRef ref, String current) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _SymbolPickerSheet(
        current: current,
        onSelected: (symbol) {
          ref.read(botSymbolProvider.notifier).setSymbol(symbol);
          Navigator.pop(context);
        },
      ),
    );
  }
}

class _SymbolPickerSheet extends StatelessWidget {
  final String current;
  final ValueChanged<String> onSelected;

  const _SymbolPickerSheet({required this.current, required this.onSelected});

  @override
  Widget build(BuildContext context) {
    final groups = <String, List<Map<String, String>>>{
      'Volatility Index': AppConstants.volatilitySymbols,
      'Volatility (1s) Index': AppConstants.volatility1sSymbols,
      'Jump Index': AppConstants.jumpSymbols,
      'Forex & Metals': AppConstants.forexSymbols,
    };

    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.75,
      maxChildSize: 0.95,
      builder: (_, controller) => Column(
        children: [
          const SizedBox(height: 12),
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.textMuted.withOpacity(0.4),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Select Bot Trading Pair',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: ListView(
              controller: controller,
              padding: const EdgeInsets.all(16),
              children: groups.entries.map((entry) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: Text(
                        entry.key,
                        style: const TextStyle(
                          color: AppColors.primary,
                          fontWeight: FontWeight.w700,
                          fontSize: 12,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ),
                    ...entry.value.map((s) {
                      final isSelected = s['symbol'] == current;
                      return ListTile(
                        contentPadding:
                            const EdgeInsets.symmetric(horizontal: 8),
                        leading: Container(
                          width: 36,
                          height: 36,
                          decoration: BoxDecoration(
                            color: isSelected
                                ? AppColors.primary.withOpacity(0.15)
                                : AppColors.textMuted.withOpacity(0.08),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Icon(
                            Icons.show_chart,
                            size: 18,
                            color: isSelected
                                ? AppColors.primary
                                : AppColors.textMuted,
                          ),
                        ),
                        title: Text(
                          s['name']!,
                          style: TextStyle(
                            fontWeight: isSelected
                                ? FontWeight.w700
                                : FontWeight.w500,
                            color: isSelected ? AppColors.primary : null,
                          ),
                        ),
                        subtitle: Text(
                          s['symbol']!,
                          style: const TextStyle(
                              fontSize: 11, color: AppColors.textMuted),
                        ),
                        trailing: isSelected
                            ? const Icon(Icons.check_circle,
                                color: AppColors.primary)
                            : null,
                        onTap: () => onSelected(s['symbol']!),
                      );
                    }),
                    const Divider(),
                  ],
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Bot Control Strip
// ─────────────────────────────────────────────────────────────────────────────

class _BotControlStrip extends ConsumerWidget {
  final String botStatus;
  const _BotControlStrip({required this.botStatus});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifier = ref.read(botStatusProvider.notifier);
    final isRunning = botStatus == 'running';
    final isPaused  = botStatus == 'paused';

    return Row(
      children: [
        Expanded(
          child: ElevatedButton.icon(
            onPressed: isRunning || isPaused ? null : () => notifier.startBot(),
            icon: const Icon(Icons.play_arrow),
            label: const Text('Start Bot'),
            style:
                ElevatedButton.styleFrom(backgroundColor: AppColors.success),
          ),
        ),
        const SizedBox(width: 8),
        if (isRunning)
          Expanded(
            child: OutlinedButton.icon(
              onPressed: () => notifier.pauseBot(),
              icon: const Icon(Icons.pause),
              label: const Text('Pause'),
            ),
          ),
        if (isPaused)
          Expanded(
            child: OutlinedButton.icon(
              onPressed: () => notifier.resumeBot(),
              icon: const Icon(Icons.play_arrow),
              label: const Text('Resume'),
            ),
          ),
        const SizedBox(width: 8),
        Expanded(
          child: OutlinedButton.icon(
            onPressed:
                (isRunning || isPaused) ? () => notifier.stopBot() : null,
            icon: const Icon(Icons.stop),
            label: const Text('Stop'),
            style: OutlinedButton.styleFrom(foregroundColor: AppColors.danger),
          ),
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Risk status
// ─────────────────────────────────────────────────────────────────────────────

class _RiskStatusCard extends StatelessWidget {
  final Map<String, dynamic> riskData;
  const _RiskStatusCard({required this.riskData});

  @override
  Widget build(BuildContext context) {
    final emergencyStop  = riskData['emergency_stop']  as bool? ?? false;
    final tradingEnabled = riskData['trading_enabled'] as bool? ?? true;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: emergencyStop
            ? AppColors.danger.withOpacity(0.1)
            : AppColors.success.withOpacity(0.08),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: emergencyStop
              ? AppColors.danger.withOpacity(0.4)
              : AppColors.success.withOpacity(0.3),
        ),
      ),
      child: Row(
        children: [
          Icon(
            emergencyStop
                ? Icons.warning_amber_rounded
                : Icons.shield_outlined,
            color: emergencyStop ? AppColors.danger : AppColors.success,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  emergencyStop ? 'Emergency Stop Active' : 'Risk Controls OK',
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    color:
                        emergencyStop ? AppColors.danger : AppColors.success,
                  ),
                ),
                Text(
                  tradingEnabled ? 'Trading enabled' : 'Trading disabled',
                  style: const TextStyle(
                      color: AppColors.textMuted, fontSize: 12),
                ),
              ],
            ),
          ),
          TextButton(
            onPressed: () => context.go('/risk'),
            child: const Text('Settings'),
          ),
        ],
      ),
    );
  }
}

class _DashboardSkeleton extends StatelessWidget {
  const _DashboardSkeleton();
  @override
  Widget build(BuildContext context) =>
      const Center(child: CircularProgressIndicator(color: AppColors.primary));
}

class _ErrorView extends StatelessWidget {
  final String error;
  final VoidCallback onRetry;
  const _ErrorView({required this.error, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.wifi_off, size: 48, color: AppColors.textMuted),
            const SizedBox(height: 16),
            Text(error,
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.textMuted)),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}
