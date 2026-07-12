// Simple risk settings model — no code generation needed
class RiskSettingsModel {
  final int id;
  final int userId;
  final double defaultStake;
  final double maxStake;
  final double maxDailyLoss;
  final int maxDailyTrades;
  final double dailyProfitTarget;
  final int maxOpenTrades;
  final double takeProfitPct;
  final double stopLossPct;
  final bool trailingStopEnabled;
  final double trailingStopPct;
  final double maxDrawdownPct;
  final bool emergencyStop;
  final bool tradingEnabled;
  final double minAiConfidence;

  const RiskSettingsModel({
    this.id = 0,
    this.userId = 0,
    this.defaultStake = 1.0,
    this.maxStake = 10.0,
    this.maxDailyLoss = 50.0,
    this.maxDailyTrades = 20,
    this.dailyProfitTarget = 100.0,
    this.maxOpenTrades = 3,
    this.takeProfitPct = 0.85,
    this.stopLossPct = 1.0,
    this.trailingStopEnabled = false,
    this.trailingStopPct = 0.1,
    this.maxDrawdownPct = 20.0,
    this.emergencyStop = false,
    this.tradingEnabled = true,
    this.minAiConfidence = 0.65,
  });

  factory RiskSettingsModel.fromJson(Map<String, dynamic> json) {
    return RiskSettingsModel(
      id: json['id'] as int? ?? 0,
      userId: json['user_id'] as int? ?? 0,
      defaultStake: (json['default_stake'] as num?)?.toDouble() ?? 1.0,
      maxStake: (json['max_stake'] as num?)?.toDouble() ?? 10.0,
      maxDailyLoss: (json['max_daily_loss'] as num?)?.toDouble() ?? 50.0,
      maxDailyTrades: json['max_daily_trades'] as int? ?? 20,
      dailyProfitTarget: (json['daily_profit_target'] as num?)?.toDouble() ?? 100.0,
      maxOpenTrades: json['max_open_trades'] as int? ?? 3,
      takeProfitPct: (json['take_profit_pct'] as num?)?.toDouble() ?? 0.85,
      stopLossPct: (json['stop_loss_pct'] as num?)?.toDouble() ?? 1.0,
      trailingStopEnabled: json['trailing_stop_enabled'] as bool? ?? false,
      trailingStopPct: (json['trailing_stop_pct'] as num?)?.toDouble() ?? 0.1,
      maxDrawdownPct: (json['max_drawdown_pct'] as num?)?.toDouble() ?? 20.0,
      emergencyStop: json['emergency_stop'] as bool? ?? false,
      tradingEnabled: json['trading_enabled'] as bool? ?? true,
      minAiConfidence: (json['min_ai_confidence'] as num?)?.toDouble() ?? 0.65,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'user_id': userId,
        'default_stake': defaultStake,
        'max_stake': maxStake,
        'max_daily_loss': maxDailyLoss,
        'max_daily_trades': maxDailyTrades,
        'daily_profit_target': dailyProfitTarget,
        'max_open_trades': maxOpenTrades,
        'take_profit_pct': takeProfitPct,
        'stop_loss_pct': stopLossPct,
        'trailing_stop_enabled': trailingStopEnabled,
        'trailing_stop_pct': trailingStopPct,
        'max_drawdown_pct': maxDrawdownPct,
        'emergency_stop': emergencyStop,
        'trading_enabled': tradingEnabled,
        'min_ai_confidence': minAiConfidence,
      };

  RiskSettingsModel copyWith({
    double? defaultStake,
    double? maxStake,
    double? maxDailyLoss,
    int? maxDailyTrades,
    double? dailyProfitTarget,
    int? maxOpenTrades,
    double? takeProfitPct,
    double? stopLossPct,
    bool? trailingStopEnabled,
    double? trailingStopPct,
    double? maxDrawdownPct,
    bool? emergencyStop,
    bool? tradingEnabled,
    double? minAiConfidence,
  }) {
    return RiskSettingsModel(
      id: id,
      userId: userId,
      defaultStake: defaultStake ?? this.defaultStake,
      maxStake: maxStake ?? this.maxStake,
      maxDailyLoss: maxDailyLoss ?? this.maxDailyLoss,
      maxDailyTrades: maxDailyTrades ?? this.maxDailyTrades,
      dailyProfitTarget: dailyProfitTarget ?? this.dailyProfitTarget,
      maxOpenTrades: maxOpenTrades ?? this.maxOpenTrades,
      takeProfitPct: takeProfitPct ?? this.takeProfitPct,
      stopLossPct: stopLossPct ?? this.stopLossPct,
      trailingStopEnabled: trailingStopEnabled ?? this.trailingStopEnabled,
      trailingStopPct: trailingStopPct ?? this.trailingStopPct,
      maxDrawdownPct: maxDrawdownPct ?? this.maxDrawdownPct,
      emergencyStop: emergencyStop ?? this.emergencyStop,
      tradingEnabled: tradingEnabled ?? this.tradingEnabled,
      minAiConfidence: minAiConfidence ?? this.minAiConfidence,
    );
  }
}
