// Simple AI signal model — no code generation needed
class AiSignalModel {
  final String symbol;
  final String signal;
  final double confidence;
  final String reason;
  final String trend;
  final String volatility;
  final String? pattern;
  final double? entryPrice;
  final double? suggestedStake;
  final DateTime? generatedAt;

  const AiSignalModel({
    required this.symbol,
    required this.signal,
    required this.confidence,
    required this.reason,
    required this.trend,
    required this.volatility,
    this.pattern,
    this.entryPrice,
    this.suggestedStake,
    this.generatedAt,
  });

  factory AiSignalModel.fromJson(Map<String, dynamic> json) {
    return AiSignalModel(
      symbol: json['symbol'] as String? ?? '',
      signal: json['signal'] as String? ?? 'WAIT',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      reason: json['reason'] as String? ?? '',
      trend: json['trend'] as String? ?? 'SIDEWAYS',
      volatility: json['volatility'] as String? ?? 'MEDIUM',
      pattern: json['pattern'] as String?,
      entryPrice: (json['entry_price'] as num?)?.toDouble(),
      suggestedStake: (json['suggested_stake'] as num?)?.toDouble(),
      generatedAt: json['generated_at'] != null
          ? DateTime.tryParse(json['generated_at'] as String)
          : null,
    );
  }
}
