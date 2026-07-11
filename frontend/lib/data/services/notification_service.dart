import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/notification_model.dart';
import 'api_client.dart';

final notificationServiceProvider = Provider<NotificationApiService>(
  (ref) => NotificationApiService(ref.read(dioProvider)),
);

class NotificationApiService {
  final Dio _dio;
  NotificationApiService(this._dio);

  Future<List<NotificationModel>> getNotifications({
    bool unreadOnly = false,
    int limit = 50,
  }) async {
    final r = await _dio.get('/notifications', queryParameters: {
      'unread_only': unreadOnly,
      'limit': limit,
    });
    return (r.data as List)
        .map((e) => NotificationModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> markAllRead() async {
    await _dio.post('/notifications/read-all');
  }

  Future<void> deleteNotification(int id) async {
    await _dio.delete('/notifications/$id');
  }
}
