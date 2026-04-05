package com.martin.kraken.auth;

import org.springframework.stereotype.Component;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.concurrent.atomic.AtomicLong;

@Component
public class KrakenAuthenticator {

    private final AtomicLong nonceCounter = new AtomicLong(System.currentTimeMillis() * 10_000);

    /**
     * Signs a request for the Kraken Futures API.
     * <p>
     * Signature = base64( hmac_sha512( base64decode(secret), sha256(postData + nonce + endpointPath) ) )
     */
    public String sign(String base64Secret, String postData, String nonce, String endpointPath) {
        try {
            // Decode the base64 secret
            byte[] secretBytes = Base64.getDecoder().decode(base64Secret);

            // SHA-256 of (postData + nonce + endpointPath)
            String input = postData + nonce + endpointPath;
            MessageDigest sha256 = MessageDigest.getInstance("SHA-256");
            byte[] hash = sha256.digest(input.getBytes(StandardCharsets.UTF_8));

            // HMAC-SHA-512 using decoded secret as key
            Mac hmac = Mac.getInstance("HmacSHA512");
            hmac.init(new SecretKeySpec(secretBytes, "HmacSHA512"));
            byte[] signature = hmac.doFinal(hash);

            // Base64 encode the result
            return Base64.getEncoder().encodeToString(signature);
        } catch (Exception e) {
            throw new RuntimeException("Failed to sign request", e);
        }
    }

    /**
     * Generates a nonce based on current time in milliseconds.
     */
    public String generateNonce() {
        return String.valueOf(nonceCounter.incrementAndGet());
    }
}
