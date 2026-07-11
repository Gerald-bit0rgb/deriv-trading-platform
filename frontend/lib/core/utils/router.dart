import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/providers/auth_provider.dart';
import '../../presentation/screens/auth/login_screen.dart';
import '../../presentation/screens/auth/register_screen.dart';
import '../../presentation/screens/dashboard/dashboard_screen.dart';
import '../../presentation/screens/trading/trading_screen.dart';
import '../../presentation/screens/history/history_screen.dart';
import '../../presentation/screens/ai/ai_screen.dart';
import '../../presentation/screens/risk/risk_screen.dart';
import '../../presentation/screens/notifications/notifications_screen.dart';
import '../../presentation/screens/profile/profile_screen.dart';
import '../../presentation/widgets/common/main_shell.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/dashboard',
    redirect: (context, state) {
      final isAuth = authState.isAuthenticated;
      final isAuthRoute = state.matchedLocation.startsWith('/login') ||
          state.matchedLocation.startsWith('/register');

      if (!isAuth && !isAuthRoute) return '/login';
      if (isAuth && isAuthRoute) return '/dashboard';
      return null;
    },
    routes: [
      // ── Auth routes (no shell) ─────────────────────────────────────────
      GoRoute(path: '/login',    builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/register', builder: (_, __) => const RegisterScreen()),

      // ── Authenticated routes (with bottom nav shell) ───────────────────
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(path: '/dashboard',    builder: (_, __) => const DashboardScreen()),
          GoRoute(path: '/trading',      builder: (_, __) => const TradingScreen()),
          GoRoute(path: '/history',      builder: (_, __) => const HistoryScreen()),
          GoRoute(path: '/ai',           builder: (_, __) => const AiScreen()),
          GoRoute(path: '/risk',         builder: (_, __) => const RiskScreen()),
          GoRoute(path: '/notifications',builder: (_, __) => const NotificationsScreen()),
          GoRoute(path: '/profile',      builder: (_, __) => const ProfileScreen()),
        ],
      ),
    ],
  );
});
