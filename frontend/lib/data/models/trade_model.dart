import 'package:freezed_annotation/freezed_annotation.dart';

part 'trade_model.freezed.dart';
part 'trade_model.g.dart';

@freezed
class TradeModel with _$TradeModel {
  const factory TradeModel({
    required int id,
    String? contractId,
    required String symbol,
    required String contractType,
    required double stake,
    double? payout,
    double? profit,
    double? entryPrice,
    double? exitPrice,
    double? takeProfit,
    double? stopLoss,
    @Default('open') String status,
    bool? isWin,
    String? aiSignal,
    double? aiConfidence,
    String? aiReason,
    @Default('manual') String source,
    DateTime? openedAt,
    DateTime? closedAt,
  }) = _TradeModel;

  factory TradeModel.fromJson(Map<String, dynamic> json) =>
      _$TradeModelFromJson(json);
}

@freezed
class TradeSummary with _$TradeSummary {
  const factory TradeSummary({
    @Default(0) int totalTrades,
    @Default(0) int openTrades,
    @Default(0) int closedTrades,
    @Default(0.0) double totalProfit,
    @Default(0.0) double winRate,
    @Default(0.0) double lossRate,
    @Default(0.0) double todayProfit,
    @Default(0) int todayTrades,
  }) = _TradeSummary;

  factory TradeSummary.fromJson(Map<String, dynamic> json) =>
      _$TradeSummaryFromJson(json);
}
