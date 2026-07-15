// ─────────────────────────────────────────────────────────────────────────────
// App-wide constants
// ─────────────────────────────────────────────────────────────────────────────

class AppConstants {
  AppConstants._();

  // App info
  static const String appName = 'Deriv AI Trader';
  static const String appVersion = '1.0.0';

  // ── Backend API ────────────────────────────────────────────────────────────
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://deriv-trading-platform-mxic.onrender.com',
  );
  static const String apiPrefix = '/api/v1';
  static const int connectTimeoutMs = 15000;
  static const int receiveTimeoutMs = 15000;

  // ── Secure storage keys ────────────────────────────────────────────────────
  static const String accessTokenKey  = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userDataKey     = 'user_data';
  static const String themeKey        = 'app_theme';
  static const String botSymbolKey    = 'bot_symbol';

  // ── All tradeable symbols ──────────────────────────────────────────────────

  // Volatility Indices (standard)
  static const List<Map<String, String>> volatilitySymbols = [
    {'symbol': 'R_10',  'name': 'Volatility 10 Index'},
    {'symbol': 'R_25',  'name': 'Volatility 25 Index'},
    {'symbol': 'R_50',  'name': 'Volatility 50 Index'},
    {'symbol': 'R_75',  'name': 'Volatility 75 Index'},
    {'symbol': 'R_100', 'name': 'Volatility 100 Index'},
  ];

  // Volatility 1s Indices
  static const List<Map<String, String>> volatility1sSymbols = [
    {'symbol': '1HZ10V',  'name': 'Volatility 10 (1s) Index'},
    {'symbol': '1HZ25V',  'name': 'Volatility 25 (1s) Index'},
    {'symbol': '1HZ50V',  'name': 'Volatility 50 (1s) Index'},
    {'symbol': '1HZ75V',  'name': 'Volatility 75 (1s) Index'},
    {'symbol': '1HZ100V', 'name': 'Volatility 100 (1s) Index'},
  ];

  // Jump Indices
  static const List<Map<String, String>> jumpSymbols = [
    {'symbol': 'JD10',  'name': 'Jump 10 Index'},
    {'symbol': 'JD25',  'name': 'Jump 25 Index'},
    {'symbol': 'JD50',  'name': 'Jump 50 Index'},
    {'symbol': 'JD75',  'name': 'Jump 75 Index'},
    {'symbol': 'JD100', 'name': 'Jump 100 Index'},
  ];

  // Forex pairs
  static const List<Map<String, String>> forexSymbols = [
    {'symbol': 'frxEURUSD', 'name': 'EUR/USD'},
    {'symbol': 'frxGBPUSD', 'name': 'GBP/USD'},
    {'symbol': 'frxUSDJPY', 'name': 'USD/JPY'},
    {'symbol': 'frxAUDUSD', 'name': 'AUD/USD'},
    {'symbol': 'frxUSDCAD', 'name': 'USD/CAD'},
    {'symbol': 'frxXAUUSD', 'name': 'Gold/USD'},
  ];

  // All symbols combined for pickers
  static List<Map<String, String>> get allSymbols => [
        ...volatilitySymbols,
        ...volatility1sSymbols,
        ...jumpSymbols,
        ...forexSymbols,
      ];

  // Simple list of symbol strings (backward compat)
  static List<String> get popularSymbols =>
      allSymbols.map((s) => s['symbol']!).toList();

  // Default bot symbol
  static const String defaultBotSymbol = 'R_100';

  // ── Contract types (EA-style Multiplier positions) ─────────────────────────
  static const List<String> contractTypes = ['MULTUP', 'MULTDOWN'];

  // ── Multiplier (leverage) used for all bot/manual trades ───────────────────
  static const int defaultMultiplier = 100;
  static const Duration dashboardRefreshInterval = Duration(seconds: 10);

  // ── Pagination ────────────────────────────────────────────────────────────
  static const int defaultPageSize = 20;
}
