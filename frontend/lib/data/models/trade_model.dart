// Simple trade model — no code generation needed
class TradeModel {
  final int id;
  final String? contractId;
  final String symbol;
  final String contractType;
  final double stake;
  final double? payout;
  final double? profit;
  final double? entryPrice;
  final double? exitPrice;
  final double? takeProfit;
  final double? stopLoss;
  final String status;
  final bool? isWin;
  final String? aiSignal;
  final double? aiConfidence;
  final String? aiReason;
  final String source;
  final DateTime? openedAt;
  final DateTime? closedAt;

  const TradeModel({
    required this.id,
    this.contractId,
    required this.symbol,
    required this.contractType,
    required this.stake,
    this.payout,
    this.profit,
    this.entryPrice,
    this.exitPrice,
    this.takeProfit,
    this.stopLoss,
    this.status = 'open',
    this.isWin,
    this.aiSignal,
    this.aiConfidence,
    this.aiReason,
    this.source = 'manual',
    this.openedAt,
    this.closedAt,
  });

  factory TradeModel.fromJson(Map<String, dynamic> json) {
    return TradeModel(
      id: json['id'] as int? ?? 0,
      contractId: json['contract_id'] as String?,
      symbol: json['symbol'] as String? ?? '',
      contractType: json['contract_type'] as String? ?? '',
      stake: (json['stake'] as num?)?.toDouble() ?? 0.0,
      payout: (json['payout'] as num?)?.toDouble(),
      profit: (json['profit'] as num?)?.toDouble(),
      entryPrice: (json['entry_price'] as num?)?.toDouble(),
      exitPrice: (json['exit_price'] as num?)?.toDouble(),
      takeProfit: (json['take_profit'] as num?)?.toDouble(),
      stopLoss: (json['stop_loss'] as num?)?.toDouble(),
      status: json['status'] as String? ?? 'open',
      isWin: json['is_win'] as bool?,
      aiSignal: json['ai_signal'] as String?,
      aiConfidence: (json['ai_confidence'] as num?)?.toDouble(),
      aiReason: json['ai_reason'] as String?,
      source: json['source'] as String? ?? 'manual',
      openedAt: json['opened_at'] != null
          ? DateTime.tryParse(json['opened_at'] as String)
          : null,
      closedAt: json['closed_at'] != null
          ? DateTime.tryParse(json['closed_at'] as String)
          : null,
    );
  }
}

class TradeSummary {
  final int totalTrades;
  final int openTrades;
  final int closedTrades;
  final double totalProfit;
  final double winRate;
  final double lossRate;
  final double todayProfit;
  final int todayTrades;

  const TradeSummary({
    this.totalTrades = 0,
    this.openTrades = 0,
    this.closedTrades = 0,
    this.totalProfit = 0.0,
    this.winRate = 0.0,
    this.lossRate = 0.0,
    this.todayProfit = 0.0,
    this.todayTrades = 0,
  });

  factory TradeSummary.fromJson(Map<String, dynamic> json) {
    return TradeSummary(
      totalTrades: json['total_trades'] as int? ?? 0,
      openTrades: json['open_trades'] as int? ?? 0,
      closedTrades: json['closed_trades'] as int? ?? 0,
      totalProfit: (json['total_profit'] as num?)?.toDouble() ?? 0.0,
      winRate: (json['win_rate'] as num?)?.toDouble() ?? 0.0,
      lossRate: (json['loss_rate'] as num?)?.toDouble() ?? 0.0,
      todayProfit: (json['today_profit'] as num?)?.toDouble() ?? 0.0,
      todayTrades: json['today_trades'] as int? ?? 0,
    );
  }
}
