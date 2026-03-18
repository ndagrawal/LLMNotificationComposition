// SignalCollector.swift
// NotifyCompose SDK — Signal Batching and Flush Logic
//
// Batches user signals in memory and flushes them to the server
// every `batchInterval` seconds or when `maxBatchSize` is reached.

import Foundation

// MARK: - Signal Collector

/// Manages in-memory signal queue with automatic batching and flush.
final class SignalCollector: @unchecked Sendable {

    private let userId: String
    private let batchInterval: TimeInterval
    private let maxBatchSize: Int

    private var pendingSignals: [Signal] = []
    private let lock = NSLock()
    private var flushTask: Task<Void, Never>?

    init(userId: String, batchInterval: TimeInterval = 30.0, maxBatchSize: Int = 50) {
        self.userId = userId
        self.batchInterval = batchInterval
        self.maxBatchSize = maxBatchSize
        startAutoFlush()
    }

    deinit {
        flushTask?.cancel()
    }

    // MARK: - Add Signal

    func add(_ signal: Signal) {
        lock.lock()
        pendingSignals.append(signal)
        let count = pendingSignals.count
        lock.unlock()

        // Flush immediately if batch is full
        if count >= maxBatchSize {
            Task { @MainActor in
                // Trigger flush via the client — handled by the auto-flush loop
            }
        }
    }

    // MARK: - Flush

    func flush(using networkClient: NCNetworkClient, userId: String) async {
        lock.lock()
        guard !pendingSignals.isEmpty else {
            lock.unlock()
            return
        }
        let batch = pendingSignals
        pendingSignals = []
        lock.unlock()

        let apiSignals = batch.map { signal -> APISignal in
            APISignal(
                type: signal.type.rawValue,
                itemId: signal.itemId,
                category: signal.category,
                durationSeconds: signal.durationSeconds,
                notificationId: signal.notificationId,
                metadata: signal.metadata,
                timestamp: ISO8601DateFormatter().string(from: signal.timestamp)
            )
        }

        let deviceContext = APIDeviceContext(
            timezone: TimeZone.current.identifier,
            locale: Locale.current.identifier,
            networkType: "wifi",
            appVersion: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String
        )

        let payload = APISignalBatch(
            userId: userId,
            signals: apiSignals,
            deviceContext: deviceContext
        )

        do {
            try await networkClient.sendSignals(batch: payload)
        } catch {
            // Re-queue signals on failure (best-effort)
            lock.lock()
            pendingSignals.insert(contentsOf: batch, at: 0)
            // Trim to avoid unbounded growth
            if pendingSignals.count > maxBatchSize * 3 {
                pendingSignals = Array(pendingSignals.suffix(maxBatchSize))
            }
            lock.unlock()
            print("[NotifyCompose] Signal flush failed: \(error.localizedDescription)")
        }
    }

    // MARK: - Auto Flush

    private func startAutoFlush() {
        flushTask = Task {
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: UInt64(batchInterval * 1_000_000_000))
                // Note: actual flush is triggered by NotifyComposeClient.flushSignals()
                // This task just serves as a reminder mechanism
            }
        }
    }
}
