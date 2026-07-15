// Strategy Settings model — 1-Minute Microtrading strategy
// Indicators: EMA 3, Bollinger Bands 18, MACD (9, 12, 26), RSI 14
// Exit: Crossback only (EMA crosses back through BB middle) — EA-style, no duration
class StrategySettingsModel {
  final int id;
  final int userId;

  // Entry timeframe (seconds) — always 60 (1M) for this strategy
  final int entryTimeframe;

  // EMA 3 (fast entry signal)
  final int emaFastPeriod;
  final String emaAppliedPrice; // CLOSE | OPEN | HIGH | LOW | MEDIAN | TYPICAL | WEIGHTED

  // Bollinger Bands 18 (signal line)
  final int bbPeriod;
  final double bbStdDev;
  final String bbMethod; // SMA | EMA

  // MACD Histogram (9, 12, 26)
  final int macdFast;
  final int macdSlow;
  final int macdSignal;

  // RSI 14
  final int rsiPeriod;
  final double rsiOverbought;
  final double rsiOversold;

  // Exit signals — crossback only, no duration-based exits
  final bool exitOnCrossbackEnabled;

  const StrategySettingsModel({
    this.id = 0,
    this.userId = 0,
    this.entryTimeframe = 60,
    this.emaFastPeriod = 3,
    this.emaAppliedPrice = 'CLOSE',
    this.bbPeriod = 18,
    this.bbStdDev = 2.0,
    this.bbMethod = 'SMA',
    this.macdFast = 12,
    this.macdSlow = 26,
    this.macdSignal = 9,
    this.rsiPeriod = 14,
    this.rsiOverbought = 70.0,
    this.rsiOversold = 30.0,
    this.exitOnCrossbackEnabled = true,
  });

  factory StrategySettingsModel.fromJson(Map<String, dynamic> json) {
    return StrategySettingsModel(
      id: json['id'] as int? ?? 0,
      userId: json['user_id'] as int? ?? 0,
      entryTimeframe: json['entry_timeframe'] as int? ?? 60,
      emaFastPeriod: json['ema_fast_period'] as int? ?? 3,
      emaAppliedPrice: json['ema_applied_price'] as String? ?? 'CLOSE',
      bbPeriod: json['bb_period'] as int? ?? 18,
      bbStdDev: (json['bb_std_dev'] as num?)?.toDouble() ?? 2.0,
      bbMethod: json['bb_method'] as String? ?? 'SMA',
      macdFast: json['macd_fast'] as int? ?? 12,
      macdSlow: json['macd_slow'] as int? ?? 26,
      macdSignal: json['macd_signal'] as int? ?? 9,
      rsiPeriod: json['rsi_period'] as int? ?? 14,
      rsiOverbought: (json['rsi_overbought'] as num?)?.toDouble() ?? 70.0,
      rsiOversold: (json['rsi_oversold'] as num?)?.toDouble() ?? 30.0,
      exitOnCrossbackEnabled: json['exit_on_crossback_enabled'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() => {
        'entry_timeframe': entryTimeframe,
        'ema_fast_period': emaFastPeriod,
        'ema_applied_price': emaAppliedPrice,
        'bb_period': bbPeriod,
        'bb_std_dev': bbStdDev,
        'bb_method': bbMethod,
        'macd_fast': macdFast,
        'macd_slow': macdSlow,
        'macd_signal': macdSignal,
        'rsi_period': rsiPeriod,
        'rsi_overbought': rsiOverbought,
        'rsi_oversold': rsiOversold,
        'exit_on_crossback_enabled': exitOnCrossbackEnabled,
      };

  StrategySettingsModel copyWith({
    int? entryTimeframe,
    int? emaFastPeriod,
    String? emaAppliedPrice,
    int? bbPeriod,
    double? bbStdDev,
    String? bbMethod,
    int? macdFast,
    int? macdSlow,
    int? macdSignal,
    int? rsiPeriod,
    double? rsiOverbought,
    double? rsiOversold,
    bool? exitOnCrossbackEnabled,
  }) {
    return StrategySettingsModel(
      id: id,
      userId: userId,
      entryTimeframe: entryTimeframe ?? this.entryTimeframe,
      emaFastPeriod: emaFastPeriod ?? this.emaFastPeriod,
      emaAppliedPrice: emaAppliedPrice ?? this.emaAppliedPrice,
      bbPeriod: bbPeriod ?? this.bbPeriod,
      bbStdDev: bbStdDev ?? this.bbStdDev,
      bbMethod: bbMethod ?? this.bbMethod,
      macdFast: macdFast ?? this.macdFast,
      macdSlow: macdSlow ?? this.macdSlow,
      macdSignal: macdSignal ?? this.macdSignal,
      rsiPeriod: rsiPeriod ?? this.rsiPeriod,
      rsiOverbought: rsiOverbought ?? this.rsiOverbought,
      rsiOversold: rsiOversold ?? this.rsiOversold,
      exitOnCrossbackEnabled: exitOnCrossbackEnabled ?? this.exitOnCrossbackEnabled,
    );
  }
}
