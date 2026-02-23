import 'package:flutter/foundation.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

class VoiceService {
  VoiceService() : _stt = stt.SpeechToText();

  final stt.SpeechToText _stt;

  /// Whether speech recognition is available on this device
  bool speechEnabled = false;

  /// Whether initialization is currently in progress
  bool _initInProgress = false;

  /// Whether we're currently listening
  bool _isListening = false;

  /// Initialize speech recognition on app startup
  /// Should be called exactly once in initState()
  /// Returns true if initialization successful, false if failed
  Future<bool> init() async {
    // Guard against multiple concurrent initializations
    if (_initInProgress) return speechEnabled;
    if (speechEnabled) return true;

    _initInProgress = true;

    try {
      // Check if speech recognition is available on this device
      speechEnabled = await _stt.initialize(
        onError: (error) {
          // Silent failure - no callback needed, just prevents further attempts
          debugPrint('Speech initialization error: $error');
        },
        onStatus: (status) {
          // Silent status updates - no callback needed
          debugPrint('Speech status: $status');
        },
      );

      if (!speechEnabled) {
        debugPrint('Speech to text not available on this device');
      }

      return speechEnabled;
    } catch (e) {
      debugPrint('Exception during speech init: $e');
      return false;
    } finally {
      _initInProgress = false;
    }
  }

  /// Start listening for voice input
  /// onResult: Called with recognized text (including partial results)
  /// onFinalResult: Called ONLY when final result is available - triggers auto-stop
  /// onAutoStop: Called when listening stops (either auto or manual)
  /// Returns false if already listening or not initialized
  bool startListening({
    required Function(String) onResult,
    required Function(String) onFinalResult,
    required VoidCallback onAutoStop,
  }) {
    // Guard: Prevent starting if already listening or initialization pending
    if (_isListening || _initInProgress) {
      debugPrint('Cannot start: already listening or initializing');
      return false;
    }

    if (!speechEnabled) {
      debugPrint('Speech not enabled - call init() first');
      return false;
    }

    _isListening = true;

    try {
      _stt.listen(
        onResult: (result) {
          // Send all partial results
          onResult(result.recognizedWords);

          // Send final result only and trigger auto-stop
          if (result.finalResult) {
            onFinalResult(result.recognizedWords);
            // Auto-stop immediately after final result
            _cancelTimeout();
            stopListening().then((_) {
              onAutoStop();
            });
          }
        },
        listenFor: const Duration(seconds: 6),
        pauseFor: const Duration(seconds: 3),
        listenOptions: stt.SpeechListenOptions(
          partialResults: true,
          cancelOnError: true,
        ),
      );

      // Set up timeout to force stop after 5 seconds (longer than listenFor)
      // This ensures we never get stuck in listening state
      Future.delayed(const Duration(seconds: 5), () {
        if (_isListening) {
          debugPrint('Voice timeout - force stopping');
          stopListening().then((_) {
            onAutoStop();
          });
        }
      });

      return true;
    } catch (e) {
      debugPrint('Error starting listening: $e');
      _isListening = false;
      return false;
    }
  }

  /// Stop listening
  /// Safe to call even if not listening
  Future<void> stopListening() async {
    _cancelTimeout();

    if (!_isListening) {
      return;
    }

    try {
      await _stt.stop();
    } catch (e) {
      debugPrint('Error stopping speech: $e');
    } finally {
      _isListening = false;
    }
  }

  /// Cancel the forced stop timeout
  void _cancelTimeout() {
    // Timeout is handled fire-and-forget directly in delayed Future inside startListening
  }

  /// Get current listening state
  bool get isListening => _isListening;

  /// Clean up resources (if needed)
  Future<void> dispose() async {
    _cancelTimeout();
    await stopListening();
  }
}
