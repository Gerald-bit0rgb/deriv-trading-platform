import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_client.dart';

final dashboardServiceProvider = Provider<DashboardService>(
  (ref) => DashboardService(ref.read(dioProvider)),
);

class DashboardService {
  final Dio _dio;
  DashboardService(this._dio);

  Future<Map<String, dynamic>> getDashboard() async {
    final r = await _dio.get('/dashboard');
    return r.data as Map<String, dynamic>;
  }
}
