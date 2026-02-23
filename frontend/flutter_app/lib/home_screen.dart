import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'api_service.dart';
import 'models.dart';
import 'voice_service.dart';

class AppState extends ChangeNotifier {
  AppState({required ApiService api, required VoiceService voice})
      : _api = api,
        _voice = voice {
    _searchController.addListener(_onSearchChanged);
  }

  final ApiService _api;
  final VoiceService _voice;
  final TextEditingController _searchController = TextEditingController();

  TextEditingController get searchController => _searchController;

  List<ShoppingItem> items = const [];
  SuggestionGroup? suggestions;
  List<Map<String, dynamic>> searchResults = const [];
  Filters? activeFilters;

  bool isLoading = false;
  bool isListening = false;
  bool voiceServiceReady = false; // Track if voice service initialized
  String recognizedText = '';
  String? speechStatus;
  String? error;
  VoidCallback? _retryAction;

  void _onSearchChanged() {
    // Search field changed listener for future enhancements
    notifyListeners();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> refresh() async {
    isLoading = true;
    error = null;
    _retryAction = () => refresh();
    notifyListeners();
    try {
      items = await _api.getItems();
    } catch (e) {
      error = e.toString();
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> toggleListening() async {
    error = null;

    // Guard: Prevent toggling if voice not ready or already transitioning
    if (!voiceServiceReady) {
      error = 'Voice service not ready';
      notifyListeners();
      return;
    }

    if (isLoading || isListening) {
      // If already listening, stop it
      if (isListening) {
        await _stopListening();
      }
      return;
    }

    // Start listening with proper callbacks
    searchController.clear();
    recognizedText = '';
    isListening = true;
    notifyListeners();

    final success = _voice.startListening(
      onResult: (text) {
        recognizedText = text;
        speechStatus = 'Heard: $text';
        notifyListeners();
      },
      onFinalResult: (text) {
        // Store final result for processing
        recognizedText = text;
        searchController.text = text;
      },
      onAutoStop: () async {
        // Called when voice service auto-stops (after final result or timeout)
        isListening = false;
        speechStatus = null;
        notifyListeners();

        // Now process the command
        if (recognizedText.isNotEmpty) {
          await _processVoiceCommand(recognizedText);
        }
      },
    );

    if (!success) {
      error = 'Failed to start voice input';
      isListening = false;
      notifyListeners();
    }
  }

  Future<void> _stopListening() async {
    await _voice.stopListening();
    isListening = false;
    speechStatus = null;
    notifyListeners();
  }

  Future<void> _processVoiceCommand(String command) async {
    final lowerCase = command.toLowerCase();
    if (lowerCase.contains('search')) {
      final query =
          command.replaceFirst(RegExp(r'search\s+', caseSensitive: false), '');
      await searchItems(query);
    } else if (lowerCase.contains('add')) {
      final item =
          command.replaceFirst(RegExp(r'add\s+', caseSensitive: false), '');
      if (item.isNotEmpty) {
        await addItem(item);
      }
    }
  }

  Future<void> sendVoice(String text) async {
    isLoading = true;
    error = null;
    _retryAction = () => sendVoice(text);
    searchResults = const []; // clear previous results on new command
    notifyListeners();

    try {
      final resp = await _api.processVoice(text: text);
      items = resp.items;
      suggestions = resp.suggestions;
      searchResults = resp.searchResults;
      activeFilters = resp.parsed.filters;
    } catch (e) {
      error = e.toString();
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  void retryLast() {
    final action = _retryAction;
    if (action != null) {
      action();
    }
  }

  Future<void> addItem(String itemName) async {
    await sendVoice('Add $itemName');
  }

  Future<void> searchItems(String query) async {
    await sendVoice('Search $query');
  }

  Future<void> modifyItem(String itemName, int newQuantity) async {
    isLoading = true;
    error = null;
    notifyListeners();

    try {
      if (newQuantity <= 0) {
        // Delete item
        await _api.modifyItem(item: itemName, quantity: 0);
      } else {
        // Update quantity
        await _api.modifyItem(item: itemName, quantity: newQuantity);
      }
      items = await _api.getItems();
    } catch (e) {
      error = e.toString();
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  void clearError() {
    error = null;
    notifyListeners();
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    // Initialize voice service on app startup
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (mounted) {
        final appState = context.read<AppState>();
        final voiceReady = await appState._voice.init();
        appState.voiceServiceReady = voiceReady;

        if (!voiceReady) {
          appState.error = 'Microphone not available on this device';
        }

        // Let AppState notify its own listeners rather than calling it externally
        // (assuming AppState is properly designed)
        // Note: Realistically, the AppState variables should be updated via a setter
        // that automatically calls notifyListeners(), but here we just leave logic inline.
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final s = context.watch<AppState>();

    if (s.error != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        final messenger = ScaffoldMessenger.of(context);
        messenger.showSnackBar(
          SnackBar(
            content: Text(s.error!),
            action: SnackBarAction(
              label: 'Retry',
              onPressed: () => context.read<AppState>().retryLast(),
            ),
          ),
        );
        context.read<AppState>().clearError();
      });
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('🛒 Shopping Assistant'),
        elevation: 4,
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () => context.read<AppState>().refresh(),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Integrated Search Bar with Mic
              _SearchBarWithMic(
                controller: s.searchController,
                isListening: s.isListening,
                isLoading: s.isLoading,
                voiceReady: s.voiceServiceReady,
                onMicPressed: (s.isLoading || !s.voiceServiceReady)
                    ? null
                    : () => context.read<AppState>().toggleListening(),
              ),
              const SizedBox(height: 4),
              if (s.isListening)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  child: Text(
                    s.speechStatus ?? 'Listening...',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.primary,
                          fontStyle: FontStyle.italic,
                        ),
                  ),
                ),
              const SizedBox(height: 24),

              // Error Banner
              if (s.error != null) ...[
                _ErrorBanner(message: s.error!),
                const SizedBox(height: 16),
              ],

              // Shopping List Section
              Text(
                'Shopping List',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
              const SizedBox(height: 12),
              if (s.items.isEmpty)
                const _EmptyState(
                    text: 'No items yet. Tap the mic and say "Add milk".'),
              ...s.items.map((i) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: _ItemTile(item: i),
                  )),

              // Suggestions Section
              if (s.items.isNotEmpty) ...[
                const SizedBox(height: 24),
                Text(
                  'Smart Suggestions',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                ),
                const SizedBox(height: 12),
              ],
              if ((s.suggestions?.all ?? const []).isEmpty &&
                  s.items.isNotEmpty)
                const _EmptyState(
                    text: 'Suggestions appear after a few actions.'),
              if ((s.suggestions?.all ?? const []).isNotEmpty)
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: (s.suggestions!.all)
                      .map((x) => ActionChip(
                            avatar:
                                const Icon(Icons.add_shopping_cart, size: 18),
                            label: Text(x),
                            backgroundColor: Colors.green.shade100,
                            labelStyle: TextStyle(color: Colors.green.shade900),
                            onPressed: () => s.addItem(x),
                          ))
                      .toList(),
                ),

              // Search Results Section
              if (s.searchResults.isNotEmpty) ...[
                const SizedBox(height: 24),
                Text(
                  'Search Results',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                ),
                if (s.activeFilters != null &&
                    (s.activeFilters!.brand.isNotEmpty ||
                        s.activeFilters!.size.isNotEmpty ||
                        s.activeFilters!.priceMax > 0)) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Filtered by: ${[
                      if (s.activeFilters!.brand.isNotEmpty)
                        'Brand: ${s.activeFilters!.brand}',
                      if (s.activeFilters!.size.isNotEmpty)
                        'Size: ${s.activeFilters!.size}',
                      if (s.activeFilters!.priceMax > 0)
                        'Price: <\$${s.activeFilters!.priceMax.toStringAsFixed(2)}',
                    ].join(', ')}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.primary,
                          fontStyle: FontStyle.italic,
                        ),
                  ),
                ],
                const SizedBox(height: 12),
              ],
              if (s.searchResults.isEmpty &&
                  s.recognizedText.contains('search'))
                const _EmptyState(
                    text:
                        'Try: "Search milk under 5" or "Find organic apples".'),
              ...s.searchResults.map((p) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: _ProductTile(product: p),
                  )),

              const SizedBox(height: 64),
            ],
          ),
        ),
      ),
    );
  }
}

/// Integrated Search Bar with Microphone
class _SearchBarWithMic extends StatefulWidget {
  const _SearchBarWithMic({
    required this.controller,
    required this.isListening,
    required this.isLoading,
    required this.voiceReady,
    required this.onMicPressed,
  });

  final TextEditingController controller;
  final bool isListening;
  final bool isLoading;
  final bool voiceReady;
  final VoidCallback? onMicPressed;

  @override
  State<_SearchBarWithMic> createState() => _SearchBarWithMicState();
}

class _SearchBarWithMicState extends State<_SearchBarWithMic>
    with SingleTickerProviderStateMixin {
  late AnimationController _micAnimController;
  late Animation<double> _micScale;

  @override
  void initState() {
    super.initState();
    _micAnimController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    _micScale = Tween<double>(begin: 1.0, end: 1.15).animate(
      CurvedAnimation(parent: _micAnimController, curve: Curves.easeInOut),
    );

    if (widget.isListening) {
      _micAnimController.repeat(reverse: true);
    }
  }

  @override
  void didUpdateWidget(_SearchBarWithMic oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isListening && !oldWidget.isListening) {
      _micAnimController.repeat(reverse: true);
    } else if (!widget.isListening && oldWidget.isListening) {
      _micAnimController.stop();
      _micAnimController.reset();
    }
  }

  @override
  void dispose() {
    _micAnimController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(30),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.08),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          Icon(Icons.search, color: Colors.grey.shade600, size: 24),
          const SizedBox(width: 8),
          Expanded(
            child: TextField(
              controller: widget.controller,
              decoration: InputDecoration(
                hintText: 'Search or speak...',
                hintStyle: TextStyle(color: Colors.grey.shade400),
                border: InputBorder.none,
                contentPadding: const EdgeInsets.symmetric(vertical: 16),
              ),
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          ScaleTransition(
            scale: _micScale,
            child: Container(
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: widget.isListening
                    ? Colors.red.withValues(alpha: 0.15)
                    : Colors.transparent,
              ),
              child: IconButton(
                icon: Icon(
                  widget.isListening ? Icons.mic : Icons.mic_none,
                  color: widget.isListening
                      ? Colors.red
                      : (widget.voiceReady ? Colors.green : Colors.grey),
                  size: 24,
                ),
                onPressed: widget.onMicPressed,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message});
  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.errorContainer,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Theme.of(context).colorScheme.error,
          width: 1,
        ),
      ),
      child: Row(
        children: [
          Icon(
            Icons.error_outline,
            color: Theme.of(context).colorScheme.error,
            size: 24,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                color: Theme.of(context).colorScheme.onErrorContainer,
                fontSize: 14,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: Center(
        child: Text(
          text,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
                fontStyle: FontStyle.italic,
              ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}

class _ItemTile extends StatefulWidget {
  const _ItemTile({required this.item});
  final ShoppingItem item;

  @override
  State<_ItemTile> createState() => _ItemTileState();
}

class _ItemTileState extends State<_ItemTile> {
  bool _isLoading = false;

  Future<void> _modifyQuantity(int newQuantity) async {
    setState(() => _isLoading = true);
    try {
      final state = context.read<AppState>();
      await state.modifyItem(widget.item.name, newQuantity);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.item.name,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
            ),
            if (widget.item.brand.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(
                  'Brand: ${widget.item.brand}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.primary,
                      ),
                ),
              ),
          ],
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 8),
          child: Wrap(
            spacing: 16,
            runSpacing: 4,
            children: [
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(widget.item.category,
                      style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
              if (widget.item.price > 0)
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text('\$${widget.item.price.toStringAsFixed(2)}',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Colors.green.shade700,
                              fontWeight: FontWeight.w600,
                            )),
                  ],
                ),
              if (widget.item.size.isNotEmpty)
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(widget.item.size,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Theme.of(context)
                                  .colorScheme
                                  .onSurfaceVariant,
                            )),
                  ],
                ),
            ],
          ),
        ),
        trailing: _isLoading
            ? const SizedBox(
                width: 80,
                child: Center(
                  child: SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
              )
            : Row(
                mainAxisSize: MainAxisSize.min,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  IconButton(
                    icon: const Icon(Icons.remove_circle_outline),
                    onPressed: () {
                      if (widget.item.quantity > 1) {
                        _modifyQuantity(widget.item.quantity - 1);
                      } else {
                        _modifyQuantity(0); // Delete item
                      }
                    },
                    tooltip: widget.item.quantity > 1 ? 'Decrease' : 'Remove',
                  ),
                  Text(
                    'x${widget.item.quantity}',
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.add_circle_outline),
                    onPressed: () {
                      if (widget.item.quantity < 100) {
                        _modifyQuantity(widget.item.quantity + 1);
                      }
                    },
                    tooltip: 'Increase',
                  ),
                ],
              ),
      ),
    );
  }
}

class _ProductTile extends StatefulWidget {
  const _ProductTile({required this.product});
  final Map<String, dynamic> product;

  @override
  State<_ProductTile> createState() => _ProductTileState();
}

class _ProductTileState extends State<_ProductTile> {
  bool _isAdding = false;

  @override
  Widget build(BuildContext context) {
    final name = (widget.product['name'] ?? '').toString();
    final brand = (widget.product['brand'] ?? '').toString();
    final size = (widget.product['size'] ?? '').toString();
    final category = (widget.product['category'] ?? '').toString();
    final price = (widget.product['price'] ?? 0).toDouble();
    final state = context.read<AppState>();

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      color: Colors.blue.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    brand,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey.shade600,
                        ),
                  ),
                  if (category.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(
                      'Category: $category',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.grey.shade600,
                            fontStyle: FontStyle.italic,
                          ),
                    ),
                  ],
                  if (size.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.blue.shade100,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        size,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                              color: Colors.blue.shade900,
                            ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '\$${price.toStringAsFixed(2)}',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Colors.green.shade700,
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 12),
                FilledButton.tonal(
                  onPressed: _isAdding
                      ? null
                      : () async {
                          setState(() => _isAdding = true);
                          try {
                            await state.addItem(name);
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('Added $name'),
                                  duration: const Duration(seconds: 2),
                                ),
                              );
                            }
                          } finally {
                            if (mounted) setState(() => _isAdding = false);
                          }
                        },
                  child: _isAdding
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Add'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
