import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/providers/auth_provider.dart';
import '../../../data/providers/dashboard_provider.dart';
import '../../widgets/common/stat_card.dart';
import '../../widgets/charts/equity_chart.dart';

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
    // Auto-refresh dashboard every 10 seconds
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
          error: (e, _) => _ErrorView(error: e.toString(), onRetry: () => ref.invalidate(dashboardProvider)),
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
    final account   = data['account']  as Map<String, dynamic>? ?? {};
    final today     = data['today']    as Map<String, dynamic>? ?? {};
    final allTime   = data['all_time'] as Map<String, dynamic>? ?? {};
    final riskData  = data['risk']     as Map<String, dynamic>? ?? {};
    final curve     = data['equity_curve'] as List<dynamic>? ?? [];

    final balance   = account['balance']  as num?;
    final currency  = account['currency'] as String? ?? 'USD';
    final todayP    = (today['profit']   as num?)?.toDouble() ?? 0;
    final winRate   = (today['win_rate'] as num?)?.toDouble() ?? 0;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // ── Balance card ─────────────────────────────────────────────────────
        _BalanceCard(
          balance: balance?.toDouble(),
          currency: currency,
          botStatus: botStatus,
        ).animate().fadeIn(duration: 300.ms),

        const SizedBox(height: 16),

        // ── Bot control strip ─────────────────────────────────────────────────
        _BotControlStrip(botStatus: botStatus),

        const SizedBox(height: 16),

        // ── Today's stats (2-col grid) ─────────────────────────────────────────
        Text('Today', style: Theme.of(context).textTheme.titleMedium?.copyWith(
          fontWeight: FontWeight.w700,
        )),
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

        // ── All-time stats ─────────────────────────────────────────────────────
        Text('All-Time', style: Theme.of(context).textTheme.titleMedium?.copyWith(
          fontWeight: FontWeight.w700,
        )),
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

        // ── Equity chart ───────────────────────────────────────────────────────
        Text('7-Day Equity Curve', style: Theme.of(context).textTheme.titleMedium?.copyWith(
          fontWeight: FontWeight.w700,
        )),
        const SizedBox(height: 8),
        EquityChart(equityCurve: curve).animate().fadeIn(delay: 200.ms),

        const SizedBox(height: 16),

        // ── Risk status card ───────────────────────────────────────────────────
        _RiskStatusCard(riskData: riskData),

        const SizedBox(height: 24),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Sub-widgets
// ─────────────────────────────────────────────────────────────────────────────

class _BalanceCard extends StatelessWidget {
  final double? balance;
  final String currency;
  final String botStatus;

  const _BalanceCard({this.balance, required this.currency, required this.botStatus});

  Color get _statusColor {
    switch (botStatus) {
      case 'running': return AppColors.success;
      case 'paused':  return AppColors.warning;
      case 'error':   return AppColors.danger;
      default:        return AppColors.textMuted;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.primary, AppColors.primaryDark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Account Balance',
                  style: TextStyle(color: Colors.white70, fontSize: 14)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: _statusColor,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      botStatus.toUpperCase(),
                      style: const TextStyle(
                          color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            balance != null ? Fmt.money(balance) : '—',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 32,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 4),
          Text(currency,
              style: const TextStyle(color: Colors.white60, fontSize: 13)),
        ],
      ),
    );
  }
}

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
            onPressed: isRunning || isPaused
                ? null
                : () => notifier.startBot(),
            icon: const Icon(Icons.play_arrow),
            label: const Text('Start Bot'),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.success),
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
            onPressed: (isRunning || isPaused) ? () => notifier.stopBot() : null,
            icon: const Icon(Icons.stop),
            label: const Text('Stop'),
            style: OutlinedButton.styleFrom(foregroundColor: AppColors.danger),
          ),
        ),
      ],
    );
  }
}

class _RiskStatusCard extends StatelessWidget {
  final Map<String, dynamic> riskData;
  const _RiskStatusCard({required this.riskData});

  @override
  Widget build(BuildContext context) {
    final emergencyStop  = riskData['emergency_stop'] as bool? ?? false;
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
            emergencyStop ? Icons.warning_amber_rounded : Icons.shield_outlined,
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
                    color: emergencyStop ? AppColors.danger : AppColors.success,
                  ),
                ),
                Text(
                  tradingEnabled ? 'Trading enabled' : 'Trading disabled',
                  style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
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
  Widget build(BuildContext context) {
    return const Center(
      child: CircularProgressIndicator(color: AppColors.primary),
    );
  }
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
            Text(error, textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.textMuted)),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}
