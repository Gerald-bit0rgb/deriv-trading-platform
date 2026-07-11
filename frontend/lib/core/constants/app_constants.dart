// ─────────────────────────────────────────────────────────────────────────────
// App-wide constants
// ─────────────────────────────────────────────────────────────────────────────

class AppConstants {
  AppConstants._();

  // App info
  static const String appName = 'Deriv AI Trader';
  static const String appVersion = '1.0.0';

  // ── Backend API ────────────────────────────────────────────────────────────
  // Change this to your Render URL after deployment
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://deriv-trading-backend.onrender.com',
  );
  static const String apiPrefix = '/api/v1';
  static const int connectTimeoutMs = 15000;
  static const int receiveTimeoutMs = 15000;

  // ── Secure storage keys ────────────────────────────────────────────────────
  static const String accessTokenKey  = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userDataKey     = 'user_data';
  static const String themeKey        = 'app_theme';

  // ── Trading ────────────────────────────────────────────────────────────────
  static const List<String> popularSymbols = [
    'R_100',   // Volatility 100 Index
    'R_75',    // Volatility 75 Index
    'R_50',    // Volatility 50 Index
    'R_25',    // Volatility 25 Index
    'R_10',    // Volatility 10 Index
    'frxEURUSD',
    'frxGBPUSD',
    'frxUSDJPY',
    'frxXAUUSD',
    'OTC_HSI',
  ];

  static const List<String> contractTypes = ['CALL', 'PUT'];

  static const List<Map<String, dynamic>> durationUnits = [
    {'label': 'Ticks', 'value': 't'},
    {'label': 'Seconds', 'value': 's'},
    {'label': 'Minutes', 'value': 'm'},
    {'label': 'Hours',   'value': 'h'},
    {'label': 'Days',    'value': 'd'},
  ];

  // ── Dashboard refresh ─────────────────────────────────────────────────────
  static const Duration dashboardRefreshInterval = Duration(seconds: 10);

  // ── Pagination ────────────────────────────────────────────────────────────
  static const int defaultPageSize = 20;
}
