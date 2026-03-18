// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.
//
// NotifyCompose — LLM-Based Intelligent Notification Composition SDK
// Implements the architectural framework from:
//   "LLM-Based Intelligent Notification Composition: From Static Personalization
//    to Context-Aware Persuasive Messaging" — Nilesh Agrawal (2026)

import PackageDescription

let package = Package(
    name: "NotifyCompose",
    platforms: [
        .iOS(.v16),
        .macOS(.v13)
    ],
    products: [
        .library(
            name: "NotifyCompose",
            targets: ["NotifyCompose"]
        )
    ],
    dependencies: [],
    targets: [
        .target(
            name: "NotifyCompose",
            dependencies: [],
            path: "Sources/NotifyCompose"
        ),
        .testTarget(
            name: "NotifyComposeTests",
            dependencies: ["NotifyCompose"],
            path: "Tests/NotifyComposeTests"
        )
    ]
)
