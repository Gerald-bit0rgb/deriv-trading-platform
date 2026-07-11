import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_theme.dart';
import '../../../data/providers/auth_provider.dart';
import '../../../data/providers/theme_provider.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  final _tokenCtrl = TextEditingController();
  bool _showToken = false;
  bool _isSavingToken = false;

  @override
  void dispose() {
    _tokenCtrl.dispose();
    super.dispose();
  }

  Future<void> _saveDerivToken() async {
    if (_tokenCtrl.text.trim().isEmpty) return;
    setState(() => _isSavingToken = true);
    final ok = await ref.read(authProvider.notifier).saveDerivToken(_tokenCtrl.text.trim());
    setState(() => _isSavingToken = false);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(ok ? 'Deriv token saved!' : 'Failed to save token'),
        backgroundColor: ok ? AppColors.success : AppColors.danger,
      ));
      if (ok) _tokenCtrl.clear();
    }
  }

  Future<void> _logout() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Sign Out'),
        content: const Text('Are you sure you want to sign out?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(context, true), child: const Text('Sign Out')),
        ],
      ),
    );
    if (confirm == true) {
      await ref.read(authProvider.notifier).logout();
      if (mounted) context.go('/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final user = authState.user;
    final themeMode = ref.watch(themeProvider);
    final isDark = themeMode == ThemeMode.dark;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ── Avatar + name ────────────────────────────────────────────────
          Center(
            child: Column(
              children: [
                CircleAvatar(
                  radius: 40,
                  backgroundColor: AppColors.primary.withOpacity(0.2),
                  child: Text(
                    (user?.username ?? '?').substring(0, 1).toUpperCase(),
                    style: const TextStyle(
                      color: AppColors.primary,
                      fontSize: 32,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  user?.fullName ?? user?.username ?? 'User',
                  style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
                ),
                Text(
                  user?.email ?? '',
                  style: const TextStyle(color: AppColors.textMuted),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // ── Deriv API Token ───────────────────────────────────────────────
          _SectionCard(
            title: 'Deriv API Token',
            icon: Icons.vpn_key_outlined,
            iconColor: AppColors.accent,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (user?.hasDerivToken == true)
                  Container(
                    padding: const EdgeInsets.all(10),
                    margin: const EdgeInsets.only(bottom: 12),
                    decoration: BoxDecoration(
                      color: AppColors.success.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.check_circle, color: AppColors.success, size: 16),
                        SizedBox(width: 8),
                        Text('Token is saved and active',
                            style: TextStyle(color: AppColors.success, fontSize: 13)),
                      ],
                    ),
                  ),
                TextField(
                  controller: _tokenCtrl,
                  obscureText: !_showToken,
                  decoration: InputDecoration(
                    labelText: 'Enter new Deriv API token',
                    hintText: 'Get from app.deriv.com → API Token',
                    suffixIcon: IconButton(
                      icon: Icon(_showToken ? Icons.visibility_off : Icons.visibility),
                      onPressed: () => setState(() => _showToken = !_showToken),
                    ),
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  'Get your token at: app.deriv.com → Account Settings → API Token\n'
                  'Required scopes: Read, Trade, Payments',
                  style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                ),
                const SizedBox(height: 12),
                ElevatedButton(
                  onPressed: _isSavingToken ? null : _saveDerivToken,
                  child: _isSavingToken
                      ? const SizedBox(height: 20, width: 20,
                          child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Text('Save Token'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // ── Appearance ────────────────────────────────────────────────────
          _SectionCard(
            title: 'Appearance',
            icon: Icons.palette_outlined,
            child: SwitchListTile(
              title: const Text('Dark Mode'),
              subtitle: const Text('Toggle light / dark theme'),
              value: isDark,
              onChanged: (_) => ref.read(themeProvider.notifier).toggle(),
              activeColor: AppColors.primary,
              contentPadding: EdgeInsets.zero,
            ),
          ),
          const SizedBox(height: 12),

          // ── Account info ───────────────────────────────────────────────────
          _SectionCard(
            title: 'Account',
            icon: Icons.person_outline,
            child: Column(
              children: [
                _InfoRow('Username', user?.username ?? '—'),
                _InfoRow('Email', user?.email ?? '—'),
                _InfoRow('Account ID', user?.derivAccountId ?? 'Not linked'),
                _InfoRow('Status', user?.isActive == true ? 'Active' : 'Inactive'),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // ── Sign out ──────────────────────────────────────────────────────
          OutlinedButton.icon(
            onPressed: _logout,
            icon: const Icon(Icons.logout),
            label: const Text('Sign Out'),
            style: OutlinedButton.styleFrom(foregroundColor: AppColors.danger),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color? iconColor;
  final Widget child;

  const _SectionCard({
    required this.title,
    required this.icon,
    this.iconColor,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: iconColor ?? AppColors.primary, size: 18),
                const SizedBox(width: 8),
                Text(title,
                    style: const TextStyle(
                        fontWeight: FontWeight.w700, fontSize: 15)),
              ],
            ),
            const SizedBox(height: 14),
            child,
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  const _InfoRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.textMuted)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
