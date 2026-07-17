// Strategy Settings model — 1-Minute Microtrading strategy
// Trend: higher-timeframe MA filter (e.g. 4H EMA 5/13) gates every entry
// Entry: EMA 3, Bollinger Bands 18, MACD (9, 12, 26), RSI 14
// Exit: Crossback (EMA crosses back through BB middle) + optional ATR SL/TP
class StrategySettingsModel {
  final int id;
  final int userId;

  // ── Trend Direction Filter (e.g. 4H EMA 5 vs EMA 13) ────────────────────────
  final bool requireTrendAlignment;
  final int trendTimeframe;      // seconds — 14400 = 4H
  final int trendFastPeriod;
  final int trendSlowPeriod;
  final String trendMaMethod;    // EMA | SMA | WMA | SMMA
  final String trendAppliedPrice; // CLOSE | OPEN | HIGH | LOW | MEDIAN | TYPICAL | WEIGHTED

  // Entry timeframe (seconds) — configurable, defaults to 60 (1M)
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

  // ATR-based Stop Loss / Take Profit (optional, off by default)
  // Independent of the trailing stop in Risk Settings — you can use either or both.
  final bool useAtrSlTp;
  final int atrPeriod;
  final double atrSlMultiplier; // stop-loss distance = ATR × this
  final double atrTpMultiplier; // take-profit distance = ATR × this

  const StrategySettingsModel({
    this.id = 0,
    this.userId = 0,
    this.requireTrendAlignment = true,
    this.trendTimeframe = 14400,
    this.trendFastPeriod = 5,
    this.trendSlowPeriod = 13,
    this.trendMaMethod = 'EMA',
    this.trendAppliedPrice = 'CLOSE',
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
    this.useAtrSlTp = false,
    this.atrPeriod = 14,
    this.atrSlMultiplier = 1.5,
    this.atrTpMultiplier = 2.0,
  });

  factory StrategySettingsModel.fromJson(Map<String, dynamic> json) {
    return StrategySettingsModel(
      id: json['id'] as int? ?? 0,
      userId: json['user_id'] as int? ?? 0,
      requireTrendAlignment: json['require_trend_alignment'] as bool? ?? true,
      trendTimeframe: json['trend_timeframe'] as int? ?? 14400,
      trendFastPeriod: json['trend_fast_period'] as int? ?? 5,
      trendSlowPeriod: json['trend_slow_period'] as int? ?? 13,
      trendMaMethod: json['trend_ma_method'] as String? ?? 'EMA',
      trendAppliedPrice: json['trend_applied_price'] as String? ?? 'CLOSE',
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
      useAtrSlTp: json['use_atr_sl_tp'] as bool? ?? false,
      atrPeriod: json['atr_period'] as int? ?? 14,
      atrSlMultiplier: (json['atr_sl_multiplier'] as num?)?.toDouble() ?? 1.5,
      atrTpMultiplier: (json['atr_tp_multiplier'] as num?)?.toDouble() ?? 2.0,
    );
  }

  Map<String, dynamic> toJson() => {
        'require_trend_alignment': requireTrendAlignment,
        'trend_timeframe': trendTimeframe,
        'trend_fast_period': trendFastPeriod,
        'trend_slow_period': trendSlowPeriod,
        'trend_ma_method': trendMaMethod,
        'trend_applied_price': trendAppliedPrice,
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
        'use_atr_sl_tp': useAtrSlTp,
        'atr_period': atrPeriod,
        'atr_sl_multiplier': atrSlMultiplier,
        'atr_tp_multiplier': atrTpMultiplier,
      };

  StrategySettingsModel copyWith({
    bool? requireTrendAlignment,
    int? trendTimeframe,
    int? trendFastPeriod,
    int? trendSlowPeriod,
    String? trendMaMethod,
    String? trendAppliedPrice,
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
    bool? useAtrSlTp,
    int? atrPeriod,
    double? atrSlMultiplier,
    double? atrTpMultiplier,
  }) {
    return StrategySettingsModel(
      id: id,
      userId: userId,
      requireTrendAlignment: requireTrendAlignment ?? this.requireTrendAlignment,
      trendTimeframe: trendTimeframe ?? this.trendTimeframe,
      trendFastPeriod: trendFastPeriod ?? this.trendFastPeriod,
      trendSlowPeriod: trendSlowPeriod ?? this.trendSlowPeriod,
      trendMaMethod: trendMaMethod ?? this.trendMaMethod,
      trendAppliedPrice: trendAppliedPrice ?? this.trendAppliedPrice,
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
      useAtrSlTp: useAtrSlTp ?? this.useAtrSlTp,
      atrPeriod: atrPeriod ?? this.atrPeriod,
      atrSlMultiplier: atrSlMultiplier ?? this.atrSlMultiplier,
      atrTpMultiplier: atrTpMultiplier ?? this.atrTpMultiplier,
    );
  }
}
