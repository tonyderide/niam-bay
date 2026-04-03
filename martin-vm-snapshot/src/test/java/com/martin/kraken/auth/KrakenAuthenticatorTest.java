package com.martin.kraken.auth;

import org.junit.jupiter.api.Test;

import java.util.Base64;

import static org.assertj.core.api.Assertions.assertThat;

class KrakenAuthenticatorTest {

    private final KrakenAuthenticator authenticator = new KrakenAuthenticator();

    @Test
    void signShouldReturnValidBase64() {
        // Generate a base64-encoded secret
        String base64Secret = Base64.getEncoder().encodeToString("test-secret-key-1234".getBytes());

        String signature = authenticator.sign(base64Secret, "postData=value", "1234567890", "/api/v3/sendorder");

        assertThat(signature).isNotBlank();
        // Verify it is valid base64 by decoding without exception
        byte[] decoded = Base64.getDecoder().decode(signature);
        assertThat(decoded).isNotEmpty();
    }

    @Test
    void signShouldProduceDifferentSignaturesForDifferentData() {
        String base64Secret = Base64.getEncoder().encodeToString("test-secret-key-1234".getBytes());

        String sig1 = authenticator.sign(base64Secret, "postData=value1", "1234567890", "/api/v3/sendorder");
        String sig2 = authenticator.sign(base64Secret, "postData=value2", "1234567890", "/api/v3/sendorder");

        assertThat(sig1).isNotEqualTo(sig2);
    }

    @Test
    void signShouldProduceDifferentSignaturesForDifferentNonces() {
        String base64Secret = Base64.getEncoder().encodeToString("test-secret-key-1234".getBytes());

        String sig1 = authenticator.sign(base64Secret, "postData=value", "1111111111", "/api/v3/sendorder");
        String sig2 = authenticator.sign(base64Secret, "postData=value", "2222222222", "/api/v3/sendorder");

        assertThat(sig1).isNotEqualTo(sig2);
    }

    @Test
    void generateNonceShouldReturnCurrentTimeMillis() {
        long before = System.currentTimeMillis();
        String nonce = authenticator.generateNonce();
        long after = System.currentTimeMillis();

        long nonceValue = Long.parseLong(nonce);
        assertThat(nonceValue).isBetween(before, after);
    }
}
