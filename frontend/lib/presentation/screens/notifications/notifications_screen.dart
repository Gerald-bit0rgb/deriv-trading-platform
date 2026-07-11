import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:timeago/timeago.dart' as timeago;

import '../../../core/theme/app_theme.dart';
import '../../../data/models/notification_model.dart';
import '../../../data/services/notification_service.dart';

final notificationsProvider =
    FutureProvider.autoDispose<List<NotificationModel>>((ref) {
  return ref.read(notificationServiceProvider).getNotifications();
});

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifAsync = ref.watch(notificationsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          TextButton(
            onPressed: () async {
              await ref.read(notificationServiceProvider).markAllRead();
              ref.invalidate(notificationsProvider);
            },
            child: const Text('Mark all read'),
          ),
        ],
      ),
      body: notifAsync.when(
        loading: () => const Center(
          child: CircularProgressIndicator(color: AppColors.primary),
        ),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (notifs) => notifs.isEmpty
            ? const Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.notifications_off_outlined,
                        size: 48, color: AppColors.textMuted),
                    SizedBox(height: 12),
                    Text('No notifications yet',
                        style: TextStyle(color: AppColors.textMuted)),
                  ],
                ),
              )
            : RefreshIndicator(
                onRefresh: () async => ref.invalidate(notificationsProvider),
                child: ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: notifs.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 4),
                  itemBuilder: (_, i) => _NotifTile(
                    notif: notifs[i],
                    onDelete: () async {
                      await ref
                          .read(notificationServiceProvider)
                          .deleteNotification(notifs[i].id);
                      ref.invalidate(notificationsProvider);
                    },
                  ),
                ),
              ),
      ),
    );
  }
}

class _NotifTile extends StatelessWidget {
  final NotificationModel notif;
  final VoidCallback onDelete;

  const _NotifTile({required this.notif, required this.onDelete});

  IconData get _icon {
    switch (notif.type) {
      case 'trade_open':   return Icons.arrow_upward;
      case 'trade_close':  return Icons.check_circle_outline;
      case 'sl_hit':       return Icons.trending_down;
      case 'tp_hit':       return Icons.emoji_events_outlined;
      case 'target_reached': return Icons.flag_outlined;
      case 'daily_loss':   return Icons.warning_amber_rounded;
      default:             return Icons.notifications_outlined;
    }
  }

  Color get _color {
    switch (notif.type) {
      case 'trade_open':     return AppColors.info;
      case 'trade_close':    return AppColors.success;
      case 'sl_hit':         return AppColors.danger;
      case 'tp_hit':         return AppColors.success;
      case 'daily_loss':     return AppColors.danger;
      case 'target_reached': return AppColors.accent;
      default:               return AppColors.textMuted;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final sentAt = notif.sentAt;

    return Dismissible(
      key: Key('notif-${notif.id}'),
      direction: DismissDirection.endToStart,
      onDismissed: (_) => onDelete(),
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 16),
        decoration: BoxDecoration(
          color: AppColors.danger.withOpacity(0.2),
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Icon(Icons.delete_outline, color: AppColors.danger),
      ),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: notif.isRead
              ? (isDark ? AppColors.darkCard : AppColors.lightCard)
              : _color.withOpacity(0.06),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: notif.isRead
                ? (isDark ? AppColors.darkBorder : AppColors.lightBorder)
                : _color.withOpacity(0.25),
          ),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: _color.withOpacity(0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(_icon, color: _color, size: 18),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(notif.title,
                      style: TextStyle(
                        fontWeight:
                            notif.isRead ? FontWeight.w500 : FontWeight.w700,
                      )),
                  const SizedBox(height: 2),
                  Text(notif.body,
                      style: const TextStyle(
                          color: AppColors.textMuted, fontSize: 13)),
                  const SizedBox(height: 4),
                  Text(
                    sentAt != null ? timeago.format(sentAt) : '',
                    style: const TextStyle(
                        color: AppColors.textMuted, fontSize: 11),
                  ),
                ],
              ),
            ),
            if (!notif.isRead)
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  color: _color,
                  shape: BoxShape.circle,
                ),
              ),
          ],
        ),
      ),
    );
  }
}
