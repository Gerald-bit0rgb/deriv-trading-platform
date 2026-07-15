// Simple AI signal model — no code generation needed
// Matches backend AISignalResponse (1-Minute Microtrading strategy)
class AiSignalModel {
  final String symbol;
  final String signal;             // BUY | SELL | WAIT
  final double confidence;         // 0.0 – 1.0
  final String reason;
  final double? ema3Value;
  final double? bbMiddle;
  final double? macdHistogram;
  final double? rsiValue;
  final String volatility;         // HIGH | MEDIUM | LOW
  final String? trendDirection;    // BULLISH | BEARISH | NEUTRAL
  final DateTime? generatedAt;

  const AiSignalModel({
    required this.symbol,
    required this.signal,
    required this.confidence,
    required this.reason,
    this.ema3Value,
    this.bbMiddle,
    this.macdHistogram,
    this.rsiValue,
    this.volatility = 'MEDIUM',
    this.trendDirection,
    this.generatedAt,
  });

  factory AiSignalModel.fromJson(Map<String, dynamic> json) {
    return AiSignalModel(
      symbol: json['symbol'] as String? ?? '',
      signal: json['signal'] as String? ?? 'WAIT',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      reason: json['reason'] as String? ?? '',
      ema3Value: (json['ema3_value'] as num?)?.toDouble(),
      bbMiddle: (json['bb_middle'] as num?)?.toDouble(),
      macdHistogram: (json['macd_histogram'] as num?)?.toDouble(),
      rsiValue: (json['rsi_value'] as num?)?.toDouble(),
      volatility: json['volatility'] as String? ?? 'MEDIUM',
      trendDirection: json['trend_direction'] as String?,
      generatedAt: json['generated_at'] != null
          ? DateTime.tryParse(json['generated_at'] as String)
          : null,
    );
  }
}
