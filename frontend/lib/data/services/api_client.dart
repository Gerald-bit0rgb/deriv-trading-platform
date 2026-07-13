import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/constants/app_constants.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Providers
// ─────────────────────────────────────────────────────────────────────────────

final secureStorageProvider = Provider<FlutterSecureStorage>(
  (_) => const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  ),
);

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(BaseOptions(
    baseUrl: '${AppConstants.baseUrl}${AppConstants.apiPrefix}',
    connectTimeout: const Duration(milliseconds: AppConstants.connectTimeoutMs),
    receiveTimeout: const Duration(milliseconds: AppConstants.receiveTimeoutMs),
    headers: {'Content-Type': 'application/json'},
  ));

  // Add auth interceptor
  dio.interceptors.add(AuthInterceptor(ref));
  return dio;
});

// ─────────────────────────────────────────────────────────────────────────────
// Auth interceptor — automatically attaches the Bearer token
// ─────────────────────────────────────────────────────────────────────────────

class AuthInterceptor extends Interceptor {
  final Ref _ref;
  AuthInterceptor(this._ref);

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final storage = _ref.read(secureStorageProvider);
    final token = await storage.read(key: AppConstants.accessTokenKey);
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    // Auto-refresh on 401
    if (err.response?.statusCode == 401) {
      final storage = _ref.read(secureStorageProvider);
      final refreshToken = await storage.read(key: AppConstants.refreshTokenKey);
      if (refreshToken != null) {
        try {
          final dio = Dio(BaseOptions(
            baseUrl: '${AppConstants.baseUrl}${AppConstants.apiPrefix}',
          ));
          final response = await dio.post('/auth/refresh', data: {
            'refresh_token': refreshToken,
          });
          final newToken = response.data['access_token'] as String;
          final newRefresh = response.data['refresh_token'] as String;
          await storage.write(key: AppConstants.accessTokenKey, value: newToken);
          await storage.write(key: AppConstants.refreshTokenKey, value: newRefresh);

          // Also update SharedPreferences so background service stays in sync
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString(AppConstants.accessTokenKey, newToken);
          await prefs.setString(AppConstants.refreshTokenKey, newRefresh);

          // Retry original request with new token
          err.requestOptions.headers['Authorization'] = 'Bearer $newToken';
          final retryResponse = await _ref
              .read(dioProvider)
              .fetch(err.requestOptions);
          handler.resolve(retryResponse);
          return;
        } catch (_) {
          // Refresh failed — clear tokens (user will be redirected to login)
          await storage.deleteAll();
        }
      }
    }
    handler.next(err);
  }
}
