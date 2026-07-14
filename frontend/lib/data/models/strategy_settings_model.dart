// Strategy Settings model — configurable MA Bias Basket parameters
class StrategySettingsModel {
  final int id;
  final int userId;

  // Bias timeframe (seconds): 3600=1H, 14400=4H, 86400=1D
  final int biasTimeframe;
  final int biasFastPeriod;
  final int biasSlowPeriod;
  final String biasMaMethod;       // EMA | SMA | WMA | SMMA
  final String biasAppliedPrice;   // CLOSE | OPEN | HIGH | LOW | MEDIAN | TYPICAL | WEIGHTED

  // ADX filter
  final bool adxEnabled;
  final int adxPeriod;
  final double adxThreshold;

  // Entry timeframe (seconds): 60=1M, 300=5M, 900=15M, 1800=30M, 3600=1H
  final int entryTimeframe;
  final int entryFastPeriod;
  final String entryFastMethod;
  final int entrySlowPeriod;
  final String entrySlowMethod;
  final String entryAppliedPrice;

  // Emergency exit
  final bool emergencyExitEnabled;
  final int exitSmaPeriod;

  // Trade duration
  final int tradeDuration;
  final String tradeDurationUnit;
  final bool requireCandleConfirmation;
  final bool maCrossExitEnabled;  // t=ticks, s=seconds, m=minutes

  const StrategySettingsModel({
    this.id = 0,
    this.userId = 0,
    this.biasTimeframe = 14400,
    this.biasFastPeriod = 5,
    this.biasSlowPeriod = 13,
    this.biasMaMethod = 'EMA',
    this.biasAppliedPrice = 'CLOSE',
    this.adxEnabled = true,
    this.adxPeriod = 14,
    this.adxThreshold = 20.0,
    this.entryTimeframe = 900,
    this.entryFastPeriod = 5,
    this.entryFastMethod = 'EMA',
    this.entrySlowPeriod = 50,
    this.entrySlowMethod = 'SMA',
    this.entryAppliedPrice = 'TYPICAL',
    this.emergencyExitEnabled = true,
    this.exitSmaPeriod = 50,
    this.tradeDuration = 5,
    this.tradeDurationUnit = 't',
    this.requireCandleConfirmation = false,
    this.maCrossExitEnabled = false,
  });

  factory StrategySettingsModel.fromJson(Map<String, dynamic> json) {
    return StrategySettingsModel(
      id: json['id'] as int? ?? 0,
      userId: json['user_id'] as int? ?? 0,
      biasTimeframe: json['bias_timeframe'] as int? ?? 14400,
      biasFastPeriod: json['bias_fast_period'] as int? ?? 5,
      biasSlowPeriod: json['bias_slow_period'] as int? ?? 13,
      biasMaMethod: json['bias_ma_method'] as String? ?? 'EMA',
      biasAppliedPrice: json['bias_applied_price'] as String? ?? 'CLOSE',
      adxEnabled: json['adx_enabled'] as bool? ?? true,
      adxPeriod: json['adx_period'] as int? ?? 14,
      adxThreshold: (json['adx_threshold'] as num?)?.toDouble() ?? 20.0,
      entryTimeframe: json['entry_timeframe'] as int? ?? 900,
      entryFastPeriod: json['entry_fast_period'] as int? ?? 5,
      entryFastMethod: json['entry_fast_method'] as String? ?? 'EMA',
      entrySlowPeriod: json['entry_slow_period'] as int? ?? 50,
      entrySlowMethod: json['entry_slow_method'] as String? ?? 'SMA',
      entryAppliedPrice: json['entry_applied_price'] as String? ?? 'TYPICAL',
      emergencyExitEnabled: json['emergency_exit_enabled'] as bool? ?? true,
      exitSmaPeriod: json['exit_sma_period'] as int? ?? 50,
      tradeDuration: json['trade_duration'] as int? ?? 5,
      tradeDurationUnit: json['trade_duration_unit'] as String? ?? 't',
      requireCandleConfirmation:
          json['require_candle_confirmation'] as bool? ?? false,
      maCrossExitEnabled:
          json['ma_cross_exit_enabled'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
        'bias_timeframe': biasTimeframe,
        'bias_fast_period': biasFastPeriod,
        'bias_slow_period': biasSlowPeriod,
        'bias_ma_method': biasMaMethod,
        'bias_applied_price': biasAppliedPrice,
        'adx_enabled': adxEnabled,
        'adx_period': adxPeriod,
        'adx_threshold': adxThreshold,
        'entry_timeframe': entryTimeframe,
        'entry_fast_period': entryFastPeriod,
        'entry_fast_method': entryFastMethod,
        'entry_slow_period': entrySlowPeriod,
        'entry_slow_method': entrySlowMethod,
        'entry_applied_price': entryAppliedPrice,
        'emergency_exit_enabled': emergencyExitEnabled,
        'exit_sma_period': exitSmaPeriod,
        'trade_duration': tradeDuration,
        'trade_duration_unit': tradeDurationUnit,
        'require_candle_confirmation': requireCandleConfirmation,
        'ma_cross_exit_enabled': maCrossExitEnabled,
      };

  StrategySettingsModel copyWith({
    int? biasTimeframe,
    int? biasFastPeriod,
    int? biasSlowPeriod,
    String? biasMaMethod,
    String? biasAppliedPrice,
    bool? adxEnabled,
    int? adxPeriod,
    double? adxThreshold,
    int? entryTimeframe,
    int? entryFastPeriod,
    String? entryFastMethod,
    int? entrySlowPeriod,
    String? entrySlowMethod,
    String? entryAppliedPrice,
    bool? emergencyExitEnabled,
    int? exitSmaPeriod,
    int? tradeDuration,
    String? tradeDurationUnit,
    bool? requireCandleConfirmation,
    bool? maCrossExitEnabled,
  }) {
    return StrategySettingsModel(
      id: id,
      userId: userId,
      biasTimeframe: biasTimeframe ?? this.biasTimeframe,
      biasFastPeriod: biasFastPeriod ?? this.biasFastPeriod,
      biasSlowPeriod: biasSlowPeriod ?? this.biasSlowPeriod,
      biasMaMethod: biasMaMethod ?? this.biasMaMethod,
      biasAppliedPrice: biasAppliedPrice ?? this.biasAppliedPrice,
      adxEnabled: adxEnabled ?? this.adxEnabled,
      adxPeriod: adxPeriod ?? this.adxPeriod,
      adxThreshold: adxThreshold ?? this.adxThreshold,
      entryTimeframe: entryTimeframe ?? this.entryTimeframe,
      entryFastPeriod: entryFastPeriod ?? this.entryFastPeriod,
      entryFastMethod: entryFastMethod ?? this.entryFastMethod,
      entrySlowPeriod: entrySlowPeriod ?? this.entrySlowPeriod,
      entrySlowMethod: entrySlowMethod ?? this.entrySlowMethod,
      entryAppliedPrice: entryAppliedPrice ?? this.entryAppliedPrice,
      emergencyExitEnabled: emergencyExitEnabled ?? this.emergencyExitEnabled,
      exitSmaPeriod: exitSmaPeriod ?? this.exitSmaPeriod,
      tradeDuration: tradeDuration ?? this.tradeDuration,
      tradeDurationUnit: tradeDurationUnit ?? this.tradeDurationUnit,
      requireCandleConfirmation:
          requireCandleConfirmation ?? this.requireCandleConfirmation,
      maCrossExitEnabled: maCrossExitEnabled ?? this.maCrossExitEnabled,
    );
  }
}
