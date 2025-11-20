package com.example.legacyapp.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import java.time.Instant;

@RestController
public class MainController {

    @GetMapping("/")
    public String home() {
        return "This is deployment 12 !! Legacy Java App is running successfully! Deployed at: " + Instant.now();
    }

    @GetMapping("/health")
    public String health() {
        return "{\"status\":\"UP\"}";
    }
}

