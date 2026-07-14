import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Bottom navigation shell shared by all authenticated screens.
class MainShell extends StatelessWidget {
  final Widget child;
  const MainShell({super.key, required this.child});

  static const _tabs = [
    _NavTab(icon: Icons.dashboard_rounded, label: 'Dashboard', path: '/dashboard'),
    _NavTab(icon: Icons.candlestick_chart, label: 'Trade',     path: '/trading'),
    _NavTab(icon: Icons.auto_awesome,      label: 'AI',        path: '/ai'),
    _NavTab(icon: Icons.playlist_add_check_rounded, label: 'Watchlist', path: '/watchlist'),
    _NavTab(icon: Icons.tune,              label: 'Strategy',  path: '/strategy'),
    _NavTab(icon: Icons.person_rounded,    label: 'Profile',   path: '/profile'),
  ];

  int _currentIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    for (int i = 0; i < _tabs.length; i++) {
      if (location.startsWith(_tabs[i].path)) return i;
    }
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex(context),
        onDestinationSelected: (i) => context.go(_tabs[i].path),
        destinations: _tabs
            .map((t) => NavigationDestination(
                  icon: Icon(t.icon),
                  label: t.label,
                ))
            .toList(),
      ),
    );
  }
}

class _NavTab {
  final IconData icon;
  final String label;
  final String path;
  const _NavTab({required this.icon, required this.label, required this.path});
}
