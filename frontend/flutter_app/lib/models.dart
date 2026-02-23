class Filters {
  final String brand;
  final double priceMax;
  final String size;

  const Filters({required this.brand, required this.priceMax, required this.size});

  factory Filters.fromJson(Map<String, dynamic> json) {
    return Filters(
      brand: (json['brand'] ?? '').toString(),
      priceMax: (json['price_max'] ?? 0).toDouble(),
      size: (json['size'] ?? '').toString(),
    );
  }
}

class ParsedVoiceCommand {
  final String action; // add/remove/modify/search
  final String item;
  final int quantity;
  final String category;
  final Filters filters;
  final String language;
  final String rawText;

  const ParsedVoiceCommand({
    required this.action,
    required this.item,
    required this.quantity,
    required this.category,
    required this.filters,
    required this.language,
    required this.rawText,
  });

  factory ParsedVoiceCommand.fromJson(Map<String, dynamic> json) {
    return ParsedVoiceCommand(
      action: (json['action'] ?? '').toString(),
      item: (json['item'] ?? '').toString(),
      quantity: (json['quantity'] ?? 1) as int,
      category: (json['category'] ?? 'other').toString(),
      filters: Filters.fromJson((json['filters'] ?? const {}) as Map<String, dynamic>),
      language: (json['language'] ?? 'en').toString(),
      rawText: (json['raw_text'] ?? '').toString(),
    );
  }
}

class ShoppingItem {
  final int id;
  final String name;
  final int quantity;
  final String category;
  final String brand;
  final double price;
  final String size;

  const ShoppingItem({
    required this.id,
    required this.name,
    required this.quantity,
    required this.category,
    this.brand = '',
    this.price = 0.0,
    this.size = '',
  });

  factory ShoppingItem.fromJson(Map<String, dynamic> json) {
    return ShoppingItem(
      id: (json['id'] ?? 0) as int,
      name: (json['name'] ?? '').toString(),
      quantity: (json['quantity'] ?? 1) as int,
      category: (json['category'] ?? 'other').toString(),
      brand: (json['brand'] ?? '').toString(),
      price: ((json['price'] ?? 0) as num).toDouble(),
      size: (json['size'] ?? '').toString(),
    );
  }
}

class SuggestionGroup {
  final List<String> previous;
  final List<String> seasonal;
  final List<String> substitutes;
  final List<String> all;

  const SuggestionGroup({
    required this.previous,
    required this.seasonal,
    required this.substitutes,
    required this.all,
  });

  factory SuggestionGroup.fromJson(Map<String, dynamic> json) {
    List<String> toList(dynamic v) =>
        (v as List<dynamic>? ?? const []).map((e) => e.toString()).toList();

    return SuggestionGroup(
      previous: toList(json['previous']),
      seasonal: toList(json['seasonal']),
      substitutes: toList(json['substitutes']),
      all: toList(json['all']),
    );
  }
}

class ProcessVoiceResponse {
  final ParsedVoiceCommand parsed;
  final List<ShoppingItem> items;
  final SuggestionGroup suggestions;
  final List<Map<String, dynamic>> searchResults;

  const ProcessVoiceResponse({
    required this.parsed,
    required this.items,
    required this.suggestions,
    required this.searchResults,
  });

  factory ProcessVoiceResponse.fromJson(Map<String, dynamic> json) {
    final itemsJson = (json['items'] as List<dynamic>? ?? const []);
    final resultsJson = (json['search_results'] as List<dynamic>? ?? const []);

    return ProcessVoiceResponse(
      parsed: ParsedVoiceCommand.fromJson((json['parsed'] ?? const {}) as Map<String, dynamic>),
      items: itemsJson.map((e) => ShoppingItem.fromJson(e as Map<String, dynamic>)).toList(),
      suggestions: SuggestionGroup.fromJson((json['suggestions'] ?? const {}) as Map<String, dynamic>),
      searchResults: resultsJson.map((e) => (e as Map<String, dynamic>)).toList(),
    );
  }
}
