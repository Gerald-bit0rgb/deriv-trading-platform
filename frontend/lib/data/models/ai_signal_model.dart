import 'package:freezed_annotation/freezed_annotation.dart';

part 'ai_signal_model.freezed.dart';
part 'ai_signal_model.g.dart';

@freezed
class AiSignalModel with _$AiSignalModel {
  const factory AiSignalModel({
    required String symbol,
    required String signal,       // BUY | SELL | WAIT
    required double confidence,
    required String reason,
    required String trend,        // BULLISH | BEARISH | SIDEWAYS
    required String volatility,   // HIGH | MEDIUM | LOW
    String? pattern,
    double? entryPrice,
    double? suggestedStake,
    DateTime? generatedAt,
  }) = _AiSignalModel;

  factory AiSignalModel.fromJson(Map<String, dynamic> json) =>
      _$AiSignalModelFromJson(json);
}
