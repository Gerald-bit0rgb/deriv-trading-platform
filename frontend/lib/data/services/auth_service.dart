import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/constants/app_constants.dart';
import '../models/user_model.dart';
import 'api_client.dart';

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService(
    ref.read(dioProvider),
    ref.read(secureStorageProvider),
  );
});

class AuthService {
  final Dio _dio;
  final FlutterSecureStorage _storage;

  AuthService(this._dio, this._storage);

  // ── Register ───────────────────────────────────────────────────────────────
  Future<AuthResponse> register({
    required String email,
    required String username,
    required String password,
    String? fullName,
  }) async {
    final response = await _dio.post('/auth/register', data: {
      'email': email,
      'username': username,
      'password': password,
      if (fullName != null) 'full_name': fullName,
    });
    final auth = AuthResponse.fromJson(response.data as Map<String, dynamic>);
    await _saveTokens(auth);
    return auth;
  }

  // ── Login ──────────────────────────────────────────────────────────────────
  Future<AuthResponse> login({
    required String email,
    required String password,
  }) async {
    final response = await _dio.post('/auth/login', data: {
      'email': email,
      'password': password,
    });
    final auth = AuthResponse.fromJson(response.data as Map<String, dynamic>);
    await _saveTokens(auth);
    return auth;
  }

  // ── Profile ────────────────────────────────────────────────────────────────
  Future<UserModel> getMe() async {
    final response = await _dio.get('/auth/me');
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  // ── Deriv token management ────────────────────────────────────────────────
  Future<UserModel> saveDerivToken(String token) async {
    final response = await _dio.put('/auth/token', data: {
      'deriv_api_token': token,
    });
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<UserModel> deleteDerivToken() async {
    final response = await _dio.delete('/auth/token');
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  // ── FCM token ─────────────────────────────────────────────────────────────
  Future<void> updateFcmToken(String fcmToken) async {
    await _dio.patch('/auth/me', data: {'fcm_token': fcmToken});
  }

  // ── Logout ─────────────────────────────────────────────────────────────────
  Future<void> logout() async {
    await _storage.deleteAll();
    // Also clear SharedPreferences so background service knows session ended
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(AppConstants.accessTokenKey);
    await prefs.remove(AppConstants.refreshTokenKey);
  }

  // ── Token helpers ──────────────────────────────────────────────────────────
  Future<void> _saveTokens(AuthResponse auth) async {
    // Save to secure storage (used by the main app)
    await _storage.write(
      key: AppConstants.accessTokenKey,
      value: auth.accessToken,
    );
    await _storage.write(
      key: AppConstants.refreshTokenKey,
      value: auth.refreshToken,
    );

    // ALSO save to SharedPreferences so the background service isolate can read it
    // Background isolate cannot access FlutterSecureStorage
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.accessTokenKey, auth.accessToken);
    await prefs.setString(AppConstants.refreshTokenKey, auth.refreshToken);
  }

  Future<bool> get isLoggedIn async {
    final token = await _storage.read(key: AppConstants.accessTokenKey);
    return token != null && token.isNotEmpty;
  }
}
