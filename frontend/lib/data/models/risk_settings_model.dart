// Simple risk settings model — no code generation needed
// Updated for lot-based EA-style trading (matches backend RiskSettings)
class RiskSettingsModel {
  final int id;
  final int userId;
  final double defaultLotSize;
  final double maxLotSize;
  final double maxDailyLoss;
  final int maxDailyTrades;
  final double dailyProfitTarget;
  final double maxDrawdownPct;
  final bool trailingStopEnabled;
  final double trailingStopDistance;
  final bool emergencyStop;
  final bool tradingEnabled;
  final double minAiConfidence;

  const RiskSettingsModel({
    this.id = 0,
    this.userId = 0,
    this.defaultLotSize = 0.01,
    this.maxLotSize = 1.0,
    this.maxDailyLoss = 50.0,
    this.maxDailyTrades = 100,
    this.dailyProfitTarget = 200.0,
    this.maxDrawdownPct = 20.0,
    this.trailingStopEnabled = true,
    this.trailingStopDistance = 2.0,
    this.emergencyStop = false,
    this.tradingEnabled = true,
    this.minAiConfidence = 0.65,
  });

  factory RiskSettingsModel.fromJson(Map<String, dynamic> json) {
    return RiskSettingsModel(
      id: json['id'] as int? ?? 0,
      userId: json['user_id'] as int? ?? 0,
      defaultLotSize: (json['default_lot_size'] as num?)?.toDouble() ?? 0.01,
      maxLotSize: (json['max_lot_size'] as num?)?.toDouble() ?? 1.0,
      maxDailyLoss: (json['max_daily_loss'] as num?)?.toDouble() ?? 50.0,
      maxDailyTrades: json['max_daily_trades'] as int? ?? 100,
      dailyProfitTarget: (json['daily_profit_target'] as num?)?.toDouble() ?? 200.0,
      maxDrawdownPct: (json['max_drawdown_pct'] as num?)?.toDouble() ?? 20.0,
      trailingStopEnabled: json['trailing_stop_enabled'] as bool? ?? true,
      trailingStopDistance: (json['trailing_stop_distance'] as num?)?.toDouble() ?? 2.0,
      emergencyStop: json['emergency_stop'] as bool? ?? false,
      tradingEnabled: json['trading_enabled'] as bool? ?? true,
      minAiConfidence: (json['min_ai_confidence'] as num?)?.toDouble() ?? 0.65,
    );
  }

  Map<String, dynamic> toJson() => {
        'default_lot_size': defaultLotSize,
        'max_lot_size': maxLotSize,
        'max_daily_loss': maxDailyLoss,
        'max_daily_trades': maxDailyTrades,
        'daily_profit_target': dailyProfitTarget,
        'max_drawdown_pct': maxDrawdownPct,
        'trailing_stop_enabled': trailingStopEnabled,
        'trailing_stop_distance': trailingStopDistance,
        'emergency_stop': emergencyStop,
        'trading_enabled': tradingEnabled,
        'min_ai_confidence': minAiConfidence,
      };

  RiskSettingsModel copyWith({
    double? defaultLotSize,
    double? maxLotSize,
    double? maxDailyLoss,
    int? maxDailyTrades,
    double? dailyProfitTarget,
    double? maxDrawdownPct,
    bool? trailingStopEnabled,
    double? trailingStopDistance,
    bool? emergencyStop,
    bool? tradingEnabled,
    double? minAiConfidence,
  }) {
    return RiskSettingsModel(
      id: id,
      userId: userId,
      defaultLotSize: defaultLotSize ?? this.defaultLotSize,
      maxLotSize: maxLotSize ?? this.maxLotSize,
      maxDailyLoss: maxDailyLoss ?? this.maxDailyLoss,
      maxDailyTrades: maxDailyTrades ?? this.maxDailyTrades,
      dailyProfitTarget: dailyProfitTarget ?? this.dailyProfitTarget,
      maxDrawdownPct: maxDrawdownPct ?? this.maxDrawdownPct,
      trailingStopEnabled: trailingStopEnabled ?? this.trailingStopEnabled,
      trailingStopDistance: trailingStopDistance ?? this.trailingStopDistance,
      emergencyStop: emergencyStop ?? this.emergencyStop,
      tradingEnabled: tradingEnabled ?? this.tradingEnabled,
      minAiConfidence: minAiConfidence ?? this.minAiConfidence,
    );
  }
}
